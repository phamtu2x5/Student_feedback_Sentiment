import os
import torch
import csv
import io
from transformers import AutoTokenizer
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from models import db, User, Feedback
from forms import RegistrationForm, LoginForm
from PhoBERTMultiTask import PhoBERTMultiTask
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
# Cấu hình
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

# Thiết lập múi giờ Việt Nam
VIETNAM_TIMEZONE = pytz.timezone('Asia/Ho_Chi_Minh')

def utc_to_vietnam_time(utc_datetime):
    """Chuyển đổi thời gian UTC sang múi giờ Việt Nam"""
    if utc_datetime is None:
        return None
    # Nếu datetime không có timezone info, coi như UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = pytz.utc.localize(utc_datetime)
    return utc_datetime.astimezone(VIETNAM_TIMEZONE)
# Sử dụng đường dẫn database phù hợp với Hugging Face Spaces
db_path = os.path.join(os.getcwd(), 'instance', 'feedback_analysis.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Khởi tạo extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Vui lòng đăng nhập để sử dụng hệ thống phân tích feedback.'
login_manager.login_message_category = 'info'

# Thêm hàm chuyển đổi múi giờ vào template context
@app.context_processor
def utility_processor():
    return dict(utc_to_vietnam_time=utc_to_vietnam_time)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Decorator để yêu cầu quyền admin
def admin_required(f):
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

# === Load tokenizer & model ===
MODEL_REPO = "Ptul2x5/Student_Feedback_Sentiment"  # 🔹 Repo Hugging Face của bạn

print("🔄 Đang tải tokenizer và model từ Hugging Face...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_REPO, use_fast=False)

# 🔹 Tải trọng số model (.bin) trực tiếp từ Hugging Face
MODEL_URL = f"https://huggingface.co/{MODEL_REPO}/resolve/main/multitask_model.bin"
state_dict = torch.hub.load_state_dict_from_url(MODEL_URL, map_location=device)

model = PhoBERTMultiTask(num_sentiment=3, num_topic=4)
model.load_state_dict(state_dict, strict=False)
model.to(device)
model.eval()

print("✅ Model đã sẵn sàng!")

# ====== ROUTES ======
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
    return jsonify({"status": "healthy", "message": "✅ PhoBERT MultiTask API is running!"})

@app.route("/my-statistics")
@login_required
def my_statistics():
    """Trang thống kê feedback cá nhân của user"""
    try:
        # Lấy thống kê feedback của user hiện tại
        user_feedbacks = Feedback.query.filter_by(user_id=current_user.id).all()
        total_feedbacks = len(user_feedbacks)
        
        # Thống kê sentiment
        sentiment_stats = db.session.query(
            Feedback.sentiment, 
            db.func.count(Feedback.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(Feedback.sentiment).all()
        sentiment_stats = [{'sentiment': item.sentiment, 'count': item.count} for item in sentiment_stats]
        
        # Thống kê topic
        topic_stats = db.session.query(
            Feedback.topic, 
            db.func.count(Feedback.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(Feedback.topic).all()
        topic_stats = [{'topic': item.topic, 'count': item.count} for item in topic_stats]
        
        # Thống kê theo ngày (30 ngày gần nhất)
        from datetime import datetime, timedelta
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
        
        # Feedback gần nhất của user
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
    """Trang xem database với giao diện đẹp"""
    try:
        # Lấy thống kê tổng quan
        total_users = User.query.count()
        total_feedbacks = Feedback.query.count()
        
        # Lấy feedbacks gần nhất
        recent_feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).limit(10).all()
        
        # Thống kê sentiment
        sentiment_stats = db.session.query(
            Feedback.sentiment, 
            db.func.count(Feedback.id).label('count')
        ).group_by(Feedback.sentiment).all()
        sentiment_stats = [{'sentiment': item.sentiment, 'count': item.count} for item in sentiment_stats]
        
        # Thống kê topic
        topic_stats = db.session.query(
            Feedback.topic, 
            db.func.count(Feedback.id).label('count')
        ).group_by(Feedback.topic).all()
        topic_stats = [{'topic': item.topic, 'count': item.count} for item in topic_stats]
        
        # Thống kê theo ngày (7 ngày gần nhất)
        from datetime import datetime, timedelta
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
    """Lấy lịch sử feedback của user hiện tại với filter thời gian"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        time_filter = request.args.get('time_filter', 'all', type=str)
        start_date = request.args.get('start_date', None, type=str)
        end_date = request.args.get('end_date', None, type=str)
        
        # Tạo query base
        query = Feedback.query.filter_by(user_id=current_user.id)
        
        # Áp dụng filter thời gian
        if time_filter != 'all':
            vietnam_now = utc_to_vietnam_time(datetime.utcnow())
            
            if time_filter == 'today':
                # Từ đầu ngày hôm nay đến hiện tại
                today_start = vietnam_now.replace(hour=0, minute=0, second=0, microsecond=0)
                today_start_utc = today_start.astimezone(pytz.utc).replace(tzinfo=None)
                query = query.filter(Feedback.created_at >= today_start_utc)
                
            elif time_filter == 'week':
                # 1 tuần trước đến hiện tại
                week_ago = vietnam_now - timedelta(days=7)
                week_ago_utc = week_ago.astimezone(pytz.utc).replace(tzinfo=None)
                query = query.filter(Feedback.created_at >= week_ago_utc)
                
            elif time_filter == 'month':
                # 1 tháng trước đến hiện tại
                month_ago = vietnam_now - timedelta(days=30)
                month_ago_utc = month_ago.astimezone(pytz.utc).replace(tzinfo=None)
                query = query.filter(Feedback.created_at >= month_ago_utc)
                
            elif time_filter == 'custom' and start_date and end_date:
                # Filter theo ngày tùy chỉnh
                try:
                    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
                    
                    # Chuyển đổi sang UTC
                    start_datetime_utc = VIETNAM_TIMEZONE.localize(start_datetime).astimezone(pytz.utc).replace(tzinfo=None)
                    end_datetime_utc = VIETNAM_TIMEZONE.localize(end_datetime.replace(hour=23, minute=59, second=59)).astimezone(pytz.utc).replace(tzinfo=None)
                    
                    query = query.filter(Feedback.created_at >= start_datetime_utc, 
                                       Feedback.created_at <= end_datetime_utc)
                except ValueError:
                    return jsonify({'error': 'Định dạng ngày không hợp lệ'}), 400
        
        # Đếm tổng số feedback theo filter (không phân trang)
        total_count = query.count()
        
        # Debug: In thông tin filter
        print(f"🔍 Filter Debug - time_filter: {time_filter}, start_date: {start_date}, end_date: {end_date}")
        print(f"🔍 Total feedbacks after filter: {total_count}")
        
        # Sắp xếp theo thời gian mới nhất và phân trang
        feedbacks = query.order_by(Feedback.created_at.desc())\
                         .paginate(page=page, per_page=per_page, error_out=False)
        
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
            'total': total_count,  # Sử dụng total_count thay vì feedbacks.total
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

        # Validate input length
        if len(text) > 1000:
            return jsonify({"error": "Text quá dài. Vui lòng nhập tối đa 1000 ký tự."}), 400

        # Tokenize
        inputs = tokenizer(
            text, return_tensors="pt", truncation=True, padding=True, max_length=128
        ).to(device)

        # Inference
        with torch.no_grad():
            logits_sent, logits_topic = model(inputs["input_ids"], inputs["attention_mask"])
            sent = torch.argmax(logits_sent, dim=1).item()
            topic = torch.argmax(logits_topic, dim=1).item()

        # Mapping
        SENTIMENT_MAP = {0: "negative", 1: "neutral", 2: "positive"}
        TOPIC_MAP = {0: "lecturer", 1: "training_program", 2: "facility", 3: "others"}
        
        sentiment = SENTIMENT_MAP[sent]
        topic_result = TOPIC_MAP[topic]
        sentiment_confidence = float(torch.softmax(logits_sent, dim=1).max().item())
        topic_confidence = float(torch.softmax(logits_topic, dim=1).max().item())

        # Lưu feedback vào database
        try:
            feedback = Feedback(
                text=text,
                sentiment=sentiment,
                topic=topic_result,
                sentiment_confidence=sentiment_confidence,
                topic_confidence=topic_confidence,
                user_id=current_user.id
            )
            db.session.add(feedback)
            db.session.commit()
        except Exception as db_error:
            print(f"Database error: {db_error}")
            # Không dừng quá trình nếu lưu DB thất bại

        return jsonify({
            "sentiment": sentiment,
            "topic": topic_result,
            "confidence": {
                "sentiment": sentiment_confidence,
                "topic": topic_confidence
            }
        })
    except Exception as e:
        return jsonify({"error": f"Có lỗi xảy ra khi xử lý: {str(e)}"}), 500


# Khởi tạo database
with app.app_context():
    db.create_all()
    
    # Kiểm tra và thêm cột is_admin nếu chưa có
    try:
        # Thử query để kiểm tra xem cột is_admin có tồn tại không
        db.session.execute(db.text("SELECT is_admin FROM users LIMIT 1"))
    except Exception:
        # Nếu cột không tồn tại, thêm cột mới
        print("🔄 Đang thêm cột is_admin vào bảng users...")
        try:
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
            db.session.commit()
            print("✅ Đã thêm cột is_admin vào database")
        except Exception as e:
            print(f"⚠️ Lỗi khi thêm cột: {e}")
    
    # Tạo tài khoản admin mặc định nếu chưa có
    try:
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(username='admin', is_admin=True)
            admin_user.set_password('123456')
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Đã tạo tài khoản admin mặc định (username: admin, password: 123456)")
        else:
            # Cập nhật user admin hiện có thành admin nếu chưa
            if not admin_user.is_admin:
                admin_user.is_admin = True
                db.session.commit()
                print("✅ Đã cập nhật tài khoản admin hiện có")
    except Exception as e:
        print(f"⚠️ Lỗi khi tạo/cập nhật admin: {e}")
    
    print("✅ Database đã sẵn sàng!")

@app.route("/analyze-csv", methods=["POST"])
@login_required
def analyze_csv():
    """Phân tích nhiều feedback từ file CSV"""
    try:
        if 'csvFile' not in request.files:
            return jsonify({'error': 'Không tìm thấy file CSV'}), 400
        
        file = request.files['csvFile']
        if file.filename == '':
            return jsonify({'error': 'Chưa chọn file'}), 400
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': 'File phải có định dạng CSV'}), 400
        
        # Đọc và validate file CSV
        try:
            # Thử decode file với UTF-8
            file_content = file.stream.read().decode("UTF8")
        except UnicodeDecodeError:
            return jsonify({'error': 'File CSV phải được mã hóa UTF-8. Vui lòng lưu file với encoding UTF-8 và thử lại.'}), 400
        
        try:
            stream = io.StringIO(file_content, newline=None)
            csv_input = csv.DictReader(stream)
            
            # Kiểm tra file có header không
            if not csv_input.fieldnames:
                return jsonify({'error': 'File CSV không có header (tên cột). Vui lòng thêm header vào file CSV.'}), 400
            
            # Tìm cột chứa feedback
            feedback_column = None
            available_columns = []
            for col in csv_input.fieldnames:
                available_columns.append(col)
                if col.lower().strip() in ['feedback', 'text', 'content', 'comment']:
                    feedback_column = col
                    break
            
            if not feedback_column:
                return jsonify({
                    'error': f'Không tìm thấy cột chứa feedback. Các cột có sẵn: {", ".join(available_columns)}. Tên cột phải là: feedback, text, content hoặc comment'
                }), 400
            
            # Kiểm tra file có dữ liệu không
            rows = list(csv_input)
            if not rows:
                return jsonify({'error': 'File CSV không có dữ liệu (chỉ có header). Vui lòng thêm dữ liệu vào file.'}), 400
                
        except csv.Error as e:
            return jsonify({'error': f'File CSV không đúng định dạng: {str(e)}. Vui lòng kiểm tra lại file CSV.'}), 400
        except Exception as e:
            return jsonify({'error': f'Lỗi khi đọc file CSV: {str(e)}'}), 400
        
        feedbacks = []
        results = []
        processed_count = 0
        error_count = 0
        
        for row_num, row in enumerate(rows, start=1):  # Bắt đầu từ 1 vì hiển thị số dòng thực tế (trừ header)
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
                # Phân tích feedback
                inputs = tokenizer(feedback_text, return_tensors="pt", padding=True, truncation=True, max_length=512)
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    # Gọi model với đúng parameters
                    sentiment_logits, topic_logits = model(inputs["input_ids"], inputs["attention_mask"])
                    
                    sentiment_probs = torch.softmax(sentiment_logits, dim=-1)
                    topic_probs = torch.softmax(topic_logits, dim=-1)
                    
                    sentiment_pred = torch.argmax(sentiment_probs, dim=-1).item()
                    topic_pred = torch.argmax(topic_probs, dim=-1).item()
                    
                    sentiment_confidence = sentiment_probs[0][sentiment_pred].item()
                    topic_confidence = topic_probs[0][topic_pred].item()
                
                # Map predictions
                sentiment_labels = ['negative', 'neutral', 'positive']
                topic_labels = ['lecturer', 'training_program', 'facility', 'others']
                
                sentiment = sentiment_labels[sentiment_pred]
                topic = topic_labels[topic_pred]
                
                # Lưu vào database
                try:
                    feedback = Feedback(
                        text=feedback_text,
                        sentiment=sentiment,
                        topic=topic,
                        sentiment_confidence=sentiment_confidence,
                        topic_confidence=topic_confidence,
                        user_id=current_user.id
                    )
                    db.session.add(feedback)
                    feedbacks.append(feedback)
                    
                    results.append({
                        'row': row_num,
                        'text': feedback_text[:100] + '...' if len(feedback_text) > 100 else feedback_text,
                        'sentiment': sentiment,
                        'topic': topic,
                        'sentiment_confidence': round(sentiment_confidence * 100, 1),
                        'topic_confidence': round(topic_confidence * 100, 1),
                        'success': True
                    })
                    
                    processed_count += 1
                    
                except Exception as db_error:
                    print(f"Database error for row {row_num}: {db_error}")
                    error_count += 1
                    results.append({
                        'row': row_num,
                        'text': feedback_text[:100] + '...' if len(feedback_text) > 100 else feedback_text,
                        'error': f'Lỗi lưu database: {str(db_error)}'
                    })
                
            except Exception as e:
                error_count += 1
                results.append({
                    'row': row_num,
                    'text': feedback_text[:100] + '...' if len(feedback_text) > 100 else feedback_text,
                    'error': f'Lỗi phân tích: {str(e)}'
                })
        
        # Commit tất cả feedback vào database
        try:
            db.session.commit()
            print(f"✅ Đã lưu {processed_count} feedback vào database")
        except Exception as commit_error:
            db.session.rollback()
            print(f"❌ Lỗi khi commit database: {commit_error}")
            return jsonify({
                'error': f'Lỗi khi lưu dữ liệu: {str(commit_error)}'
            }), 500
        
        return jsonify({
            'success': True,
            'total_rows': len(results),
            'processed_count': processed_count,
            'error_count': error_count,
            'results': results[:50],  # Chỉ trả về 50 kết quả đầu tiên để tránh response quá lớn
            'message': f'Đã xử lý {processed_count}/{len(results)} feedback thành công'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f'Có lỗi xảy ra khi xử lý file CSV: {str(e)}'
        }), 500

if __name__ == "__main__":
    # Hugging Face Spaces configuration
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=7860, debug=debug)