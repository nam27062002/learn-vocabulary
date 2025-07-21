# 🚀 DEPLOYMENT CHECKLIST - RENDER

## ❌ CURRENT ISSUE: DATABASE_URL Missing

**Error:** `ValueError: No support for ''. We support: cockroach, mssql, ...`

**Cause:** DATABASE_URL environment variable is empty or not set on Render.

**✅ FIXED:** Updated `settings_production.py` to handle missing DATABASE_URL gracefully.

## 🔧 IMMEDIATE FIX STEPS

### 1. Set Environment Variables on Render
Go to your Render service dashboard → Environment tab and add:

```
SECRET_KEY=django-insecure-your-new-secret-key-here-make-it-long-and-random
DJANGO_SETTINGS_MODULE=learn_english_project.settings_production
EMAIL_HOST_USER=nam27062002@gmail.com
EMAIL_HOST_PASSWORD=xorn xvut fsif kljt
```

### 2. Add PostgreSQL Database (IMPORTANT!)
- In Render dashboard: New → PostgreSQL
- Name: `learn-english-db`
- Copy the **Internal Database URL**
- Add as environment variable: `DATABASE_URL=postgresql://...`

### 3. Update Build Settings
**Build Command:**
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Start Command:**
```bash
gunicorn learn_english_project.wsgi:application
```

## Chuẩn bị trước khi deploy

### 1. Tạo tài khoản Render
- Đăng ký tại https://render.com
- Kết nối với GitHub repository của bạn

### 2. Push code lên GitHub
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 3. Cấu hình trên Render Dashboard

#### Tạo Database (PostgreSQL)
1. Vào Render Dashboard → New → PostgreSQL
2. Đặt tên: `learn-english-db`
3. Database Name: `learn_english_db`
4. User: `learn_english_user`
5. Chọn Free tier
6. Tạo database

#### Tạo Web Service
1. Vào Render Dashboard → New → Web Service
2. Kết nối với GitHub repo của bạn
3. Cấu hình:
   - Name: `learn-english-app`
   - Environment: `Python`
   - Build Command: `./build.sh`
   - Start Command: `gunicorn learn_english_project.wsgi:application`

#### Environment Variables
Thêm các biến môi trường sau:
- `DATABASE_URL`: Tự động từ database
- `SECRET_KEY`: Auto-generate
- `DJANGO_SETTINGS_MODULE`: `learn_english_project.settings_production`
- `EMAIL_HOST_USER`: `nam27062002@gmail.com` (hoặc email của bạn)
- `EMAIL_HOST_PASSWORD`: `xorn xvut fsif kljt` (hoặc app password của bạn)

### 4. Cấu hình Google OAuth (nếu cần)
1. Vào Google Cloud Console
2. Cập nhật Authorized redirect URIs:
   - `https://your-app-name.onrender.com/accounts/google/login/callback/`
3. Cập nhật Authorized JavaScript origins:
   - `https://your-app-name.onrender.com`

### 5. Sau khi deploy thành công
1. Tạo superuser:
   ```bash
   # Trong Render shell
   python manage.py createsuperuser
   ```
2. Kiểm tra admin panel: `https://your-app.onrender.com/admin/`
3. Test các chức năng chính

## Troubleshooting

### Lỗi thường gặp:
1. **Build failed**: Kiểm tra requirements.txt và Python version
2. **Database connection**: Kiểm tra DATABASE_URL
3. **Static files**: Kiểm tra WhiteNoise configuration
4. **Email**: Kiểm tra email credentials

### Debug commands:
```bash
# Xem logs
render logs --service your-service-name

# Connect to shell
render shell --service your-service-name
```

## Files đã tạo cho deployment:
- ✅ `build.sh` - Build script
- ✅ `render.yaml` - Render configuration
- ✅ `runtime.txt` - Python version
- ✅ `settings_production.py` - Production settings
- ✅ Updated `requirements.txt` - Added production dependencies

## Lưu ý bảo mật:
- SECRET_KEY được generate tự động
- Email credentials nên dùng environment variables
- Debug mode đã tắt trong production
- HTTPS được bật tự động