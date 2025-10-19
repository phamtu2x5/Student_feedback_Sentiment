import os
import torch
from transformers import AutoTokenizer
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Feedback
from forms import RegistrationForm, LoginForm
from PhoBERTMultiTask import PhoBERTMultiTask

app = Flask(__name__)
# Cấu hình
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

@app.route("/api/feedback-history", methods=["GET"])
@login_required
def get_feedback_history():
    """Lấy lịch sử feedback của user hiện tại"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Lấy feedback của user hiện tại, sắp xếp theo thời gian mới nhất
        feedbacks = Feedback.query.filter_by(user_id=current_user.id)\
                                 .order_by(Feedback.created_at.desc())\
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
                'created_at': feedback.created_at.isoformat()
            })
        
        return jsonify({
            'feedbacks': feedback_list,
            'total': feedbacks.total,
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
    print("✅ Database đã sẵn sàng!")

if __name__ == "__main__":
    # Hugging Face Spaces configuration
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=7860, debug=debug)