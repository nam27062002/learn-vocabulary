# 🚨 QUICK FIX - DATABASE_URL Error

## Lỗi hiện tại:
```
ValueError: No support for ''. We support: cockroach, mssql, ...
```

## ✅ Đã sửa trong code:
- Updated `settings_production.py` để handle DATABASE_URL rỗng
- Thêm fallback về SQLite nếu không có PostgreSQL

## 🔧 Cần làm ngay trên Render:

### 1. Tạo PostgreSQL Database
1. Vào Render Dashboard
2. Click "New" → "PostgreSQL"  
3. Tên: `learn-english-db`
4. Chọn Free tier
5. Click "Create Database"

### 2. Lấy Database URL
1. Vào database vừa tạo
2. Copy "Internal Database URL"
3. Nó sẽ có dạng: `postgresql://user:password@host:port/database`

### 3. Set Environment Variables
Vào Web Service → Environment tab, thêm:

```
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=django-insecure-[run python generate_secret_key.py to get this]
DJANGO_SETTINGS_MODULE=learn_english_project.settings_production
EMAIL_HOST_USER=nam27062002@gmail.com
EMAIL_HOST_PASSWORD=xorn xvut fsif kljt
```

### 4. Generate Secret Key
Chạy lệnh này để tạo secret key:
```bash
python generate_secret_key.py
```

### 5. Redeploy
Sau khi set xong environment variables, click "Manual Deploy" để deploy lại.

## 📞 Nếu vẫn lỗi:
1. Check Render logs để xem lỗi cụ thể
2. Đảm bảo DATABASE_URL được copy chính xác
3. Kiểm tra tất cả environment variables đã được set

## 🎯 Kết quả mong đợi:
- App deploy thành công
- Database kết nối OK
- Có thể truy cập website