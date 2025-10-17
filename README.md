# Student Feedback Sentiment Analysis API

Hệ thống phân tích sentiment và topic cho feedback của sinh viên sử dụng PhoBERT Multi-Task Learning, được deploy trên Render.

## 🚀 Tính năng

- **Sentiment Analysis**: Phân loại sentiment thành 3 loại (positive, neutral, negative)
- **Topic Classification**: Phân loại chủ đề thành 4 loại (lecturer, training_program, facility, others)
- **Multi-task Learning**: Xử lý cả 2 nhiệm vụ cùng lúc với một model duy nhất
- **RESTful API**: Giao diện API đơn giản và dễ sử dụng
- **Vietnamese Support**: Tối ưu cho tiếng Việt với PhoBERT
- **Production Ready**: Được tối ưu cho deployment trên cloud

## 🛠️ Cài đặt Local

1. **Clone repository:**

```bash
git clone <repository-url>
cd Student_feedback_Sentiment
```

2. **Cài đặt dependencies:**

```bash
pip install -r requirements.txt
```

3. **Chạy ứng dụng:**

```bash
python app.py
```

API sẽ chạy tại: `http://localhost:10000`

## 🚀 Deployment trên Render

### Bước 1: Chuẩn bị Repository

1. Push code lên GitHub repository
2. Đảm bảo có các file cần thiết:
   - `app.py` - Flask application
   - `PhoBERTMultiTask.py` - Model architecture
   - `requirements.txt` - Dependencies
   - `render.yaml` - Render configuration
   - `phobert_multitask_model/` - Model files

### Bước 2: Deploy trên Render

1. Đăng nhập vào [Render](https://render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub repository
4. Render sẽ tự động detect `render.yaml` và cấu hình:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Python Version**: 3.9.16

### Bước 3: Kiểm tra Deployment

- Render sẽ tự động build và deploy
- Thời gian build: ~5-10 phút (do download model)
- URL sẽ có dạng: `https://phobert-multitask-api.onrender.com`

## 📖 API Usage

### Base URL (Production)

```
https://phobert-multitask-api.onrender.com
```

### Endpoints

#### Health Check

```http
GET /
```

#### Predict Sentiment & Topic

```http
POST /predict
Content-Type: application/json
```

**Request:**

```json
{
  "text": "Giảng viên giảng bài rất hay và dễ hiểu"
}
```

**Response:**

```json
{
  "sentiment": "positive",
  "topic": "lecturer"
}
```

### Test API

**Sử dụng curl:**

```bash
# Test health check
curl https://phobert-multitask-api.onrender.com/

# Test prediction
curl -X POST https://phobert-multitask-api.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Thầy cô giảng bài rất hay và dễ hiểu"}'
```

**Sử dụng Python:**

```python
import requests

# Test prediction
response = requests.post(
    'https://phobert-multitask-api.onrender.com/predict',
    json={'text': 'Phòng học rất rộng rãi và thoáng mát'}
)
print(response.json())
```

## 📁 Cấu trúc Project

```
Student_feedback_Sentiment/
├── app.py                    # Flask API server
├── PhoBERTMultiTask.py       # Model architecture
├── phobert_multitask_model/  # Pre-trained model files
│   ├── multitask_model.bin   # Model weights
│   ├── config.json          # Model configuration
│   └── tokenizer files...   # PhoBERT tokenizer
├── requirements.txt         # Production dependencies
├── render.yaml             # Render deployment config
└── README.md               # Documentation
```

## 🏗️ Model Architecture

- **Base Model**: PhoBERT-base (vinai/phobert-base)
- **Architecture**: Multi-task learning với 2 classification heads
- **Input**: Vietnamese text (max 128 tokens)
- **Output**:
  - Sentiment: 3 classes (negative, neutral, positive)
  - Topic: 4 classes (lecturer, training_program, facility, others)

## 📊 Performance

- **Model Size**: ~440MB (PhoBERT-base + custom heads)
- **Cold Start**: ~30-60s (first request after idle)
- **Warm Requests**: ~100-200ms per request
- **Memory Usage**: ~1-2GB RAM
- **Accuracy**:
  - Sentiment: ~85-90% (validation set)
  - Topic: ~80-85% (validation set)

## 🔧 Production Optimizations

- **Gunicorn WSGI Server**: Thay thế Flask dev server
- **Minimal Dependencies**: Chỉ giữ lại packages cần thiết
- **Environment Variables**: Tự động detect PORT từ Render
- **Error Handling**: Comprehensive error responses
- **Health Check**: Endpoint để monitor service

## 🚨 Troubleshooting

### Render Deployment Issues

1. **Build Timeout**: Model download mất quá nhiều thời gian

   - Solution: Upgrade lên paid plan hoặc optimize model size

2. **Memory Issues**: Out of memory khi load model

   - Solution: Upgrade lên plan có nhiều RAM hơn

3. **Cold Start**: Request đầu tiên chậm
   - Solution: Sử dụng Render Cron Jobs để keep-alive

### Common Errors

- **502 Bad Gateway**: Service chưa sẵn sàng, đợi thêm vài phút
- **Timeout**: Model loading mất thời gian, retry request
- **Memory Error**: Upgrade Render plan

## 💡 Tips for Production

1. **Monitor Usage**: Theo dõi Render dashboard
2. **Set Alerts**: Cấu hình alerts cho downtime
3. **Backup Model**: Lưu trữ model files ở nơi an toàn
4. **Version Control**: Tag releases khi deploy
5. **Logging**: Monitor application logs

## 📞 Support

- **Render Dashboard**: Monitor service status
- **Render Logs**: Check application logs
- **GitHub Issues**: Report bugs và feature requests

---

⭐ **Project được tối ưu cho production deployment trên Render!** ⭐
