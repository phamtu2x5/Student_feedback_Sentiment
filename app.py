import os
import torch
import csv
import io
import atexit
import schedule
import time
from threading import Thread
from transformers import AutoTokenizer
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from models import db, User, Feedback
from forms import RegistrationForm, LoginForm
from PhoBERTPairABSA import PhoBERTPairABSA
from datetime import datetime, timedelta
import pytz
from database_manager import db_manager
from model_config import (
    get_prompt, ASPECTS_EN, ASPECTS_VI, LABEL_MAP, MAX_LEN, PRED_THRESHOLD,
    MIN_SENT_PROB, MIN_MARGIN,
    _is_garbage, _aspect_has_kw, _has_any_kw, _norm_match, ASPECT_REVERSE_MAPPING,
    BASE_MODEL, NUM_CLASSES, DROPOUT
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

def backup_database(force: bool = False):
    """Backup database to Hugging Face Hub"""
    try:
        return db_manager.backup_database(force=force)
    except Exception:
        return False

def restore_database():
    """Restore database from Hugging Face Hub"""
    try:
        return db_manager.restore_database()
    except Exception:
        return False

def run_scheduler():
    """Run scheduled backup every hour"""
    while True:
        schedule.run_pending()
        time.sleep(60)

schedule.every().hour.do(backup_database)
scheduler_thread = Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()
atexit.register(backup_database)

VIETNAM_TIMEZONE = pytz.timezone('Asia/Ho_Chi_Minh')

def utc_to_vietnam_time(utc_datetime):
    """Chuyển đổi thời gian UTC sang múi giờ Việt Nam"""
    if utc_datetime is None:
        return None
    if utc_datetime.tzinfo is None:
        utc_datetime = pytz.utc.localize(utc_datetime)
    return utc_datetime.astimezone(VIETNAM_TIMEZONE)

db_path = os.path.join(os.getcwd(), 'instance', 'feedback_analysis.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Vui lòng đăng nhập để sử dụng hệ thống phân tích feedback.'
login_manager.login_message_category = 'info'

@app.context_processor
def utility_processor():
    return dict(utc_to_vietnam_time=utc_to_vietnam_time)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def analyze_feedback(text):
    """Phân tích feedback với model Pair-ABSA"""
    if tokenizer is None or model is None:
        return []
    
    text = str(text).strip()
    if _is_garbage(text):
        return []
    
    s_norm = _norm_match(text)
    
    tau_len = float(PRED_THRESHOLD)
    
    logits_list = []
    has_keywords = []
    
    with torch.no_grad():
        for aspect_en in ASPECTS_EN:
            aspect_vi = ASPECT_REVERSE_MAPPING.get(aspect_en, "khac")
            prompt = get_prompt(aspect_en, sentence=text, use_subprompt=True)
            
            inputs = tokenizer(
                prompt, text,
                return_tensors="pt", 
                truncation="only_second",  # Chỉ cắt text (second sequence), giữ nguyên prompt
                padding=True, 
                max_length=MAX_LEN
            ).to(device)
            
            logits = model(inputs["input_ids"], inputs["attention_mask"]).squeeze(0)
            logits_list.append(logits)
            has_keywords.append(_aspect_has_kw(aspect_vi, s_norm))
    
    logits_tensor = torch.stack(logits_list, dim=0)
    
    probs = torch.softmax(logits_tensor, dim=-1)
    p_none = probs[:, 0]
    conf_not_none = 1.0 - p_none
    
    # Giảm cường độ boost để tránh false positive từ keywords
    KW_BOOST = 0.02  # Giảm từ 0.05 xuống 0.02 (từ 5% xuống 2%)
    conf_not_none_boosted = conf_not_none.clone()
    for i, has_kw in enumerate(has_keywords):
        if has_kw:
            conf_not_none_boosted[i] = min(1.0, conf_not_none_boosted[i] + KW_BOOST)
    
    # Bước 1: Lọc aspects có confidence >= threshold VÀ có keywords
    # Nếu không có keywords, cần confidence cao hơn nhiều (>= 0.85)
    keep_indices = []
    for i in range(len(ASPECTS_EN)):
        if has_keywords[i]:
            # Có keywords: cần confidence >= threshold
            if conf_not_none_boosted[i] >= tau_len:
                keep_indices.append(i)
        else:
            # Không có keywords: cần confidence rất cao (>= 0.85)
            if conf_not_none_boosted[i] >= 0.85:
                keep_indices.append(i)
    
    # Bước 2: Kiểm tra xem có aspect nào có confidence rất cao không (>95%)
    high_confidence_indices = [i for i in keep_indices if conf_not_none_boosted[i] >= 0.95]
    
    # Bước 3: Nếu có aspect với confidence rất cao, loại bỏ các aspects khác không có keywords
    if len(high_confidence_indices) > 0:
        # Loại bỏ các aspects không có keywords nếu đã có aspect khác có confidence rất cao
        keep_indices = [i for i in keep_indices if has_keywords[i] or i in high_confidence_indices]
        
        # Nếu vẫn còn slot, có thể thêm aspects khác nếu có keywords VÀ confidence đủ cao
        if len(keep_indices) < len(ASPECTS_EN):
            tau_len_adjusted = tau_len - 0.05  # Chỉ giảm 5%
            for i in range(len(ASPECTS_EN)):
                if i not in keep_indices:
                    # Chỉ giữ nếu có keywords VÀ confidence >= adjusted + 0.10
                    if has_keywords[i] and conf_not_none_boosted[i] >= tau_len_adjusted + 0.10:
                        keep_indices.append(i)
    
    if not keep_indices:
        return []
    
    results = []
    for i in sorted(keep_indices, key=lambda j: float(conf_not_none_boosted[j]), reverse=True):
        sent_probs = probs[i, 1:].clone()
        top_idx = int(torch.argmax(sent_probs).item())
        top_p = float(sent_probs[top_idx].item())
        
        sent_probs[top_idx] = -1.0
        second_p = float(sent_probs.max().item())
        margin = top_p - second_p
        
        min_margin_adj = MIN_MARGIN
        if has_keywords[i]:
            min_margin_adj = MIN_MARGIN - 0.02
        
        if top_p < MIN_SENT_PROB or margin < min_margin_adj:
            continue
        
        sentiment_str = LABEL_MAP[top_idx + 1]
        results.append({
            "topic": ASPECTS_EN[i],
            "sentiment": sentiment_str,
            "confidence": float(conf_not_none_boosted[i].item()),
            "sentiment_confidence": top_p,
            "margin": margin
        })
    
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results

def save_feedback_to_db(text, results, user_id):
    """Lưu feedback results vào database"""
    for result in results:
        sentiment_conf = result.get('sentiment_confidence', result['confidence'])
        topic_conf = result['confidence']
        feedback = Feedback(
            text=text,
            sentiment=result['sentiment'],
            topic=result['topic'],
            sentiment_confidence=sentiment_conf,
            topic_confidence=topic_conf,
            user_id=user_id
        )
        db.session.add(feedback)

def admin_required(f):
    """Decorator để yêu cầu quyền admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        if not current_user.is_admin:
            flash('Bạn không có quyền truy cập trang này. Chỉ admin mới được phép.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_REPO = "Ptul2x5/Student_Feedback_Sentiment"

try:
    os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
    tokenizer = AutoTokenizer.from_pretrained(MODEL_REPO, use_fast=False)
    MODEL_URL = f"https://huggingface.co/{MODEL_REPO}/resolve/main/model.bin"
    loaded = torch.hub.load_state_dict_from_url(MODEL_URL, map_location=device)
    
    if isinstance(loaded, dict) and "model_state" in loaded:
        state_dict = loaded["model_state"]
    else:
        state_dict = loaded
    
    model = PhoBERTPairABSA(base_model=BASE_MODEL, num_cls=NUM_CLASSES, dropout=DROPOUT)
    model.load_state_dict(state_dict, strict=False)
    model.to(device)
    model.eval()
except Exception:
    model = None
    tokenizer = None

@app.route("/", methods=["GET"])
@login_required
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        backup_database()
        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            flash('Đăng nhập thành công!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'danger')
    
    return render_template('login.html', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất thành công!', 'info')
    return redirect(url_for('home'))

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

@app.route("/my-statistics")
@login_required
def my_statistics():
    try:
        user_feedbacks = Feedback.query.filter_by(user_id=current_user.id).all()
        total_feedbacks = len(user_feedbacks)
        
        sentiment_stats = db.session.query(
            Feedback.sentiment, 
            db.func.count(Feedback.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(Feedback.sentiment).all()
        sentiment_stats = [{'sentiment': item.sentiment, 'count': item.count} for item in sentiment_stats]
        
        topic_stats = db.session.query(
            Feedback.topic, 
            db.func.count(Feedback.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(Feedback.topic).all()
        topic_stats = [{'topic': item.topic, 'count': item.count} for item in topic_stats]
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        daily_stats = db.session.query(
            db.func.date(Feedback.created_at).label('date'),
            db.func.count(Feedback.id).label('count')
        ).filter(
            Feedback.user_id == current_user.id,
            Feedback.created_at >= thirty_days_ago
        ).group_by(
            db.func.date(Feedback.created_at)
        ).order_by('date').all()
        daily_stats = [{'date': str(item.date), 'count': item.count} for item in daily_stats]
        
        recent_feedbacks = Feedback.query.filter_by(user_id=current_user.id)\
                                       .order_by(Feedback.created_at.desc()).limit(10).all()
        
        return render_template('my_statistics.html',
                             total_feedbacks=total_feedbacks,
                             recent_feedbacks=recent_feedbacks,
                             sentiment_stats=sentiment_stats,
                             topic_stats=topic_stats,
                             daily_stats=daily_stats)
    except Exception as e:
        flash(f'Lỗi khi tải dữ liệu: {str(e)}', 'danger')
        return redirect(url_for('home'))

@app.route("/admin/database")
@admin_required
def view_database():
    try:
        total_users = User.query.count()
        total_feedbacks = Feedback.query.count()
        recent_feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).limit(10).all()
        
        sentiment_stats = db.session.query(
            Feedback.sentiment, 
            db.func.count(Feedback.id).label('count')
        ).group_by(Feedback.sentiment).all()
        sentiment_stats = [{'sentiment': item.sentiment, 'count': item.count} for item in sentiment_stats]
        
        topic_stats = db.session.query(
            Feedback.topic, 
            db.func.count(Feedback.id).label('count')
        ).group_by(Feedback.topic).all()
        topic_stats = [{'topic': item.topic, 'count': item.count} for item in topic_stats]
        
        seven_days_ago = datetime.now() - timedelta(days=7)
        daily_stats = db.session.query(
            db.func.date(Feedback.created_at).label('date'),
            db.func.count(Feedback.id).label('count')
        ).filter(Feedback.created_at >= seven_days_ago).group_by(
            db.func.date(Feedback.created_at)
        ).order_by('date').all()
        daily_stats = [{'date': str(item.date), 'count': item.count} for item in daily_stats]
        
        return render_template('database_view.html',
                             total_users=total_users,
                             total_feedbacks=total_feedbacks,
                             recent_feedbacks=recent_feedbacks,
                             sentiment_stats=sentiment_stats,
                             topic_stats=topic_stats,
                             daily_stats=daily_stats)
    except Exception as e:
        flash(f'Lỗi khi tải dữ liệu: {str(e)}', 'danger')
        return redirect(url_for('home'))

@app.route("/api/feedback-history", methods=["GET"])
@login_required
def get_feedback_history():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        time_filter = request.args.get('time_filter', 'all', type=str)
        start_date = request.args.get('start_date', None, type=str)
        end_date = request.args.get('end_date', None, type=str)
        
        query = Feedback.query.filter_by(user_id=current_user.id)
        
        if time_filter != 'all':
            vietnam_now = utc_to_vietnam_time(datetime.utcnow())
            
            if time_filter == 'today':
                today_start = vietnam_now.replace(hour=0, minute=0, second=0, microsecond=0)
                today_start_utc = today_start.astimezone(pytz.utc).replace(tzinfo=None)
                query = query.filter(Feedback.created_at >= today_start_utc)
            elif time_filter == 'week':
                week_ago = vietnam_now - timedelta(days=7)
                week_ago_utc = week_ago.astimezone(pytz.utc).replace(tzinfo=None)
                query = query.filter(Feedback.created_at >= week_ago_utc)
            elif time_filter == 'month':
                month_ago = vietnam_now - timedelta(days=30)
                month_ago_utc = month_ago.astimezone(pytz.utc).replace(tzinfo=None)
                query = query.filter(Feedback.created_at >= month_ago_utc)
            elif time_filter == 'custom' and start_date and end_date:
                try:
                    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
                    start_datetime_utc = VIETNAM_TIMEZONE.localize(start_datetime).astimezone(pytz.utc).replace(tzinfo=None)
                    end_datetime_utc = VIETNAM_TIMEZONE.localize(end_datetime.replace(hour=23, minute=59, second=59)).astimezone(pytz.utc).replace(tzinfo=None)
                    query = query.filter(Feedback.created_at >= start_datetime_utc, Feedback.created_at <= end_datetime_utc)
                except ValueError:
                    return jsonify({'error': 'Định dạng ngày không hợp lệ'}), 400
        
        total_count = query.count()
        feedbacks = query.order_by(Feedback.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        
        feedback_list = []
        for feedback in feedbacks.items:
            feedback_list.append({
                'id': feedback.id,
                'text': feedback.text,
                'sentiment': feedback.sentiment,
                'topic': feedback.topic,
                'sentiment_confidence': feedback.sentiment_confidence,
                'topic_confidence': feedback.topic_confidence,
                'created_at': utc_to_vietnam_time(feedback.created_at).strftime('%H:%M:%S %d/%m/%Y')
            })
        
        return jsonify({
            'feedbacks': feedback_list,
            'total': total_count,
            'pages': feedbacks.pages,
            'current_page': page,
            'has_next': feedbacks.has_next,
            'has_prev': feedbacks.has_prev
        })
    except Exception as e:
        return jsonify({"error": f"Có lỗi xảy ra: {str(e)}"}), 500

@app.route("/predict", methods=["POST"])
@login_required
def predict():
    try:
        data = request.get_json()
        text = data.get("text", "").strip()

        if not text:
            return jsonify({"error": "Missing 'text' field"}), 400

        if len(text) > 1000:
            return jsonify({"error": "Text quá dài. Vui lòng nhập tối đa 1000 ký tự."}), 400

        if tokenizer is None or model is None:
            return jsonify({"error": "Model or tokenizer not loaded. Please restart the application."}), 500

        results = analyze_feedback(text)

        try:
            save_feedback_to_db(text, results, current_user.id)
            db.session.commit()
            backup_database()
        except Exception:
            pass

        return jsonify({
            "results": results,
            "has_multiple_topics": len(results) > 1
        })
    except Exception as e:
        return jsonify({"error": f"Có lỗi xảy ra khi xử lý: {str(e)}"}), 500

@app.route('/admin/backup', methods=['POST'])
@admin_required
def manual_backup():
    try:
        if backup_database():
            return jsonify({"success": True, "message": "Backup completed successfully"})
        else:
            return jsonify({"success": False, "message": "Backup failed"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Backup error: {str(e)}"}), 500

@app.route('/admin/restore', methods=['POST'])
@admin_required
def manual_restore():
    try:
        if restore_database():
            return jsonify({"success": True, "message": "Database restored successfully"})
        else:
            return jsonify({"success": False, "message": "Restore failed"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Restore error: {str(e)}"}), 500

with app.app_context():
    db_manager.initialize_database_if_needed()
    db.create_all()
    db_manager.backup_database()
    
    try:
        db.session.execute(db.text("SELECT is_admin FROM users LIMIT 1"))
    except Exception:
        try:
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
            db.session.commit()
        except Exception:
            pass
    
    try:
        total_users = User.query.count()
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user and total_users == 0:
            admin_user = User(username='admin', is_admin=True)
            admin_user.set_password('123456')
            db.session.add(admin_user)
            db.session.commit()
        elif admin_user and not admin_user.is_admin:
            admin_user.is_admin = True
            db.session.commit()
    except Exception:
        pass

@app.route("/analyze-csv", methods=["POST"])
@login_required
def analyze_csv():
    try:
        if 'csvFile' not in request.files:
            return jsonify({'error': 'Không tìm thấy file CSV'}), 400
        
        file = request.files['csvFile']
        if file.filename == '':
            return jsonify({'error': 'Chưa chọn file'}), 400
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': 'File phải có định dạng CSV'}), 400
        
        try:
            file_content = file.stream.read().decode("UTF8")
        except UnicodeDecodeError:
            return jsonify({'error': 'File CSV phải được mã hóa UTF-8'}), 400
        
        try:
            stream = io.StringIO(file_content, newline=None)
            csv_input = csv.DictReader(stream)
            
            if not csv_input.fieldnames:
                return jsonify({'error': 'File CSV không có header'}), 400
            
            feedback_column = None
            available_columns = []
            for col in csv_input.fieldnames:
                available_columns.append(col)
                if col.lower().strip() in ['feedback', 'text', 'content', 'comment']:
                    feedback_column = col
                    break
            
            if not feedback_column:
                return jsonify({
                    'error': f'Không tìm thấy cột chứa feedback. Các cột: {", ".join(available_columns)}'
                }), 400
            
            rows = list(csv_input)
            if not rows:
                return jsonify({'error': 'File CSV không có dữ liệu'}), 400
        except csv.Error as e:
            return jsonify({'error': f'File CSV không đúng định dạng: {str(e)}'}), 400
        except Exception as e:
            return jsonify({'error': f'Lỗi khi đọc file CSV: {str(e)}'}), 400
        
        results = []
        processed_count = 0
        error_count = 0
        
        for row_num, row in enumerate(rows, start=1):
            feedback_text = row[feedback_column].strip()
            
            if not feedback_text:
                error_count += 1
                results.append({
                    'row': row_num,
                    'text': '',
                    'error': 'Feedback trống'
                })
                continue
            
            try:
                if tokenizer is None or model is None:
                    results.append({
                        "row": row_num,
                        "feedback": feedback_text,
                        "error": "Model or tokenizer not loaded"
                    })
                    continue
                
                row_topics = analyze_feedback(feedback_text)
                
                try:
                    save_feedback_to_db(feedback_text, row_topics, current_user.id)
                    
                    if row_topics:
                        first = row_topics[0]
                        first_topic = first['topic']
                        first_sentiment = first['sentiment']
                        first_sentiment_conf = first.get('sentiment_confidence', first['confidence'])
                        first_topic_conf = first['confidence']
                    else:
                        first_topic = 'others'
                        first_sentiment = 'neutral'
                        first_sentiment_conf = 0.0
                        first_topic_conf = 0.0
                    
                    results.append({
                        'row': row_num,
                        'text': feedback_text[:100] + '...' if len(feedback_text) > 100 else feedback_text,
                        'sentiment': first_sentiment,
                        'topic': first_topic,
                        'sentiment_confidence': round(first_sentiment_conf * 100, 1),
                        'topic_confidence': round(first_topic_conf * 100, 1),
                        'success': True
                    })
                    processed_count += 1
                except Exception as db_err:
                    error_count += 1
                    results.append({
                        'row': row_num,
                        'text': feedback_text[:100] + '...' if len(feedback_text) > 100 else feedback_text,
                        'error': f'Lỗi lưu database: {str(db_err)}'
                    })
                
            except Exception as e:
                error_count += 1
                results.append({
                    'row': row_num,
                    'text': feedback_text[:100] + '...' if len(feedback_text) > 100 else feedback_text,
                    'error': f'Lỗi phân tích: {str(e)}'
                })
        
        try:
            db.session.commit()
            backup_database()
        except Exception as commit_error:
            db.session.rollback()
            return jsonify({'error': f'Lỗi khi lưu dữ liệu: {str(commit_error)}'}), 500
        
        return jsonify({
            'success': True,
            'total_rows': len(results),
            'processed_count': processed_count,
            'error_count': error_count,
            'results': results[:50],
            'message': f'Đã xử lý {processed_count}/{len(results)} feedback thành công'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f'Có lỗi xảy ra khi xử lý file CSV: {str(e)}'
        }), 500

if __name__ == "__main__":
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=7860, debug=debug)