import os
import shutil
import json
from datetime import datetime
from typing import Optional
from huggingface_hub import HfApi, login
import sqlite3
import tempfile

class DatabaseManager:
    def __init__(self, hf_token: Optional[str] = None, repo_id: Optional[str] = None):
        """Initialize Database Manager for Hugging Face Hub storage"""
        self.repo_id = repo_id or os.getenv('REPO_ID', 'your-username/student-feedback-db')
        self.hf_token = hf_token or os.getenv('HF_TOKEN')
        self.db_path = 'instance/feedback_analysis.db'
        self.backup_dir = 'backups'
        self.is_local = not self.hf_token
        
        os.makedirs(self.backup_dir, exist_ok=True)
        
        if self.hf_token:
            try:
                login(token=self.hf_token)
                self.api = HfApi()
            except Exception:
                self.api = None
        else:
            self.api = None
    
    def sqlite_to_json(self, db_path: str) -> dict:
        """Convert SQLite database to JSON format"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            data = {}
            
            for table in tables:
                table_name = table[0]
                
                if table_name in ['sqlite_sequence', 'sqlite_master']:
                    continue
                
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                table_data = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        if columns[i] == 'is_admin':
                            value = bool(value) if value is not None else False
                        row_dict[columns[i]] = value
                    table_data.append(row_dict)
                
                data[table_name] = {
                    'columns': columns,
                    'data': table_data
                }
            
            try:
                cursor.execute("SELECT * FROM sqlite_sequence")
                sequence_rows = cursor.fetchall()
                if sequence_rows:
                    sequence_data = []
                    for row in sequence_rows:
                        sequence_data.append({
                            'name': row[0],
                            'seq': row[1]
                        })
                    data['sqlite_sequence'] = {
                        'columns': ['name', 'seq'],
                        'data': sequence_data
                    }
            except Exception:
                pass
            
            conn.close()
            return data
        except Exception:
            return {}
    
    def json_to_sqlite(self, json_data: dict, db_path: str):
        """Convert JSON data back to SQLite database"""
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
            
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for table_name, table_info in json_data.items():
                if table_name in ['sqlite_sequence', 'sqlite_master']:
                    continue
                    
                columns = table_info['columns']
                data = table_info['data']
                
                if not columns:
                    continue
                
                column_defs = []
                for col in columns:
                    if col == 'id':
                        column_defs.append(f"{col} INTEGER PRIMARY KEY AUTOINCREMENT")
                    elif col == 'is_admin':
                        column_defs.append(f"{col} BOOLEAN DEFAULT 0")
                    else:
                        column_defs.append(f"{col} TEXT")
                
                create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
                cursor.execute(create_sql)
                
                if data:
                    placeholders = ', '.join(['?' for _ in columns])
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                    
                    for row in data:
                        values = []
                        for col in columns:
                            value = row.get(col)
                            if col == 'is_admin':
                                if isinstance(value, bool):
                                    values.append(int(value))
                                elif isinstance(value, str):
                                    values.append(1 if value.lower() in ['true', '1'] else 0)
                                else:
                                    values.append(int(value) if value else 0)
                            else:
                                values.append(value)
                        cursor.execute(insert_sql, values)
            
            if 'sqlite_sequence' in json_data:
                sequence_data = json_data['sqlite_sequence']['data']
                for seq_row in sequence_data:
                    table_name = seq_row.get('name')
                    seq_value = seq_row.get('seq')
                    if table_name and seq_value:
                        cursor.execute(f"INSERT INTO sqlite_sequence (name, seq) VALUES (?, ?)", 
                                     (table_name, seq_value))
            
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    def backup_database(self, force: bool = False) -> bool:
        """Backup database to Hugging Face Hub"""
        if self.is_local:
            return True
            
        if not self.api or not os.path.exists(self.db_path):
            return False
        
        try:
            json_data = self.sqlite_to_json(self.db_path)
            
            if not json_data:
                return False
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = f"{self.backup_dir}/feedback_backup_{timestamp}.json"
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            try:
                self.api.upload_file(
                    path_or_fileobj=temp_file,
                    path_in_repo='feedback_backup.json',
                    repo_id=self.repo_id,
                    repo_type="dataset",
                    commit_message=f"Backup database - {timestamp}"
                )
            except Exception as upload_error:
                if "No files have been modified" in str(upload_error):
                    return True
                else:
                    raise upload_error
            
            os.remove(temp_file)
            return True
        except Exception:
            return False
    
    def restore_database(self) -> bool:
        """Restore database from Hugging Face Hub"""
        if not self.api:
            return False
        
        try:
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, 'feedback_backup.json')
            
            self.api.hf_hub_download(
                repo_id=self.repo_id,
                filename='feedback_backup.json',
                local_dir=temp_dir,
                repo_type="dataset"
            )
            
            with open(temp_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            self.json_to_sqlite(json_data, self.db_path)
            shutil.rmtree(temp_dir)
            return True
        except Exception:
            return False
    
    def check_database_exists(self) -> bool:
        """Check if database file exists locally"""
        return os.path.exists(self.db_path)
    
    def initialize_database_if_needed(self):
        """Initialize database from backup if local database doesn't exist"""
        if not self.check_database_exists() and not self.is_local:
            self.restore_database()

# Global instance
db_manager = DatabaseManager()
