# Troubleshooting Render Deployment

## Lỗi Bad Gateway - Các bước debug:

### 1. Kiểm tra Render Logs
```bash
# Vào Render Dashboard → Your Service → Logs
# Hoặc dùng Render CLI:
render logs --service learn-english-app
```

### 2. Các lỗi thường gặp:

#### A. Build Failed
**Triệu chứng**: Build không thành công
**Nguyên nhân**: 
- Requirements.txt có dependencies không tương thích
- Python version không đúng

**Giải pháp**:
1. Sử dụng `requirements_minimal.txt` thay vì `requirements.txt`:
   ```bash
   # Rename files
   mv requirements.txt requirements_full.txt
   mv requirements_minimal.txt requirements.txt
   ```

2. Cập nhật runtime.txt:
   ```
   python-3.11.9
   ```

#### B. App Start Failed
**Triệu chứng**: Build thành công nhưng app không start
**Nguyên nhân**:
- Gunicorn không bind đúng port
- Settings production có lỗi
- Database connection failed

**Giải pháp**:
1. Kiểm tra start command trong render.yaml:
   ```yaml
   startCommand: "gunicorn learn_english_project.wsgi:application --bind 0.0.0.0:$PORT"
   ```

2. Kiểm tra environment variables:
   - `SECRET_KEY`: Phải được set
   - `DATABASE_URL`: Phải kết nối được với PostgreSQL
   - `DJANGO_SETTINGS_MODULE`: `learn_english_project.settings_production`

#### C. Database Connection Error
**Triệu chứng**: App start nhưng không kết nối được database
**Nguyên nhân**:
- PostgreSQL database chưa được tạo
- DATABASE_URL không đúng

**Giải pháp**:
1. Tạo PostgreSQL database trên Render
2. Kiểm tra DATABASE_URL trong environment variables
3. Chạy migrations:
   ```bash
   # Trong Render shell
   python manage.py migrate
   ```

#### D. Static Files Error
**Triệu chứng**: App chạy nhưng CSS/JS không load
**Nguyên nhân**: WhiteNoise không được cấu hình đúng

**Giải pháp**:
1. Kiểm tra MIDDLEWARE trong settings_production.py
2. Chạy collectstatic:
   ```bash
   python manage.py collectstatic --no-input
   ```

### 3. Debug Commands

#### Test production settings locally:
```bash
python test_production.py
```

#### Manual deployment test:
```bash
# Set environment variables
export DJANGO_SETTINGS_MODULE=learn_english_project.settings_production
export SECRET_KEY=your-secret-key

# Test migrations
python manage.py migrate

# Test static files
python manage.py collectstatic --no-input

# Test server start
gunicorn learn_english_project.wsgi:application --bind 0.0.0.0:8000
```

### 4. Render-specific fixes

#### Update render.yaml với minimal config:
```yaml
services:
  - type: web
    name: learn-english-app
    env: python
    buildCommand: "pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate"
    startCommand: "gunicorn learn_english_project.wsgi:application --bind 0.0.0.0:$PORT"
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: learn_english_project.settings_production
      - key: SECRET_KEY
        generateValue: true
```

#### Nếu vẫn lỗi, thử deploy manual:
1. Không dùng render.yaml
2. Tạo service manual trên dashboard
3. Set build command: `./build.sh`
4. Set start command: `gunicorn learn_english_project.wsgi:application --bind 0.0.0.0:$PORT`

### 5. Emergency fallback

Nếu vẫn không được, thử cấu hình đơn giản nhất:

1. **Tắt tất cả security settings** trong settings_production.py:
   ```python
   CSRF_COOKIE_SECURE = False
   SESSION_COOKIE_SECURE = False
   SECURE_SSL_REDIRECT = False
   ```

2. **Sử dụng SQLite thay vì PostgreSQL** (tạm thời):
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.sqlite3',
           'NAME': BASE_DIR / 'db.sqlite3',
       }
   }
   ```

3. **Tắt WhiteNoise** (tạm thời):
   ```python
   # Comment out WhiteNoise middleware
   # MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
   ```

Sau khi app chạy được, từ từ bật lại các tính năng.