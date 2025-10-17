import os
import torch
from transformers import AutoTokenizer
from flask import Flask, request, jsonify, render_template
from PhoBERTMultiTask import PhoBERTMultiTask

app = Flask(__name__)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# === Load tokenizer & model ===
MODEL_REPO = "Ptul2x5/Student_Feedback_Sentiment"  # 🔹 Repo Hugging Face của bạn

print("🔄 Đang tải tokenizer và model từ Hugging Face...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_REPO, use_fast=False)

# 🔹 Tải trọng số model (.bin) trực tiếp từ Hugging Face
state_dict = torch.hub.load_state_dict_from_url(
    f"https://huggingface.co/{MODEL_REPO}/resolve/main/multitask_model.bin",
    map_location=device
)

model = PhoBERTMultiTask(num_sentiment=3, num_topic=4)
model.load_state_dict(state_dict)
model.to(device)
model.eval()
print("✅ Model đã sẵn sàng!")

# ====== ROUTES ======
@app.route("/", methods=["GET"])
def home():
    return render_template('index.html')

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "message": "✅ PhoBERT MultiTask API is running!"})

@app.route("/predict", methods=["POST"])
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
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128).to(device)

        # Inference
        with torch.no_grad():
            logits_sent, logits_topic = model(inputs["input_ids"], inputs["attention_mask"])
            sent = torch.argmax(logits_sent, dim=1).item()
            topic = torch.argmax(logits_topic, dim=1).item()

        # Mapping
        sent_map = {0: "negative", 1: "neutral", 2: "positive"}
        topic_map = {0: "lecturer", 1: "training_program", 2: "facility", 3: "others"}

        return jsonify({
            "sentiment": sent_map[sent],
            "topic": topic_map[topic],
            "confidence": {
                "sentiment": float(torch.softmax(logits_sent, dim=1).max().item()),
                "topic": float(torch.softmax(logits_topic, dim=1).max().item())
            }
        })
    except Exception as e:
        return jsonify({"error": f"Có lỗi xảy ra khi xử lý: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
