# 🧪 Test Authentication System

## ✅ Setup đã hoàn thành!

### Google OAuth đã được cấu hình:
- ✅ Client ID: `249118040870-s9lrorcpccs80cqctvttete17pdv9ekh.apps.googleusercontent.com`
- ✅ Client Secret: Đã cài đặt
- ✅ Redirect URIs: `http://127.0.0.1:8000/accounts/google/login/callback/`
- ✅ Social Application đã được tạo trong Django

## 🚀 Cách test:

### 1. Khởi động server (nếu chưa chạy):
```bash
python manage.py runserver
```

### 2. Test Email Registration:
1. Truy cập: `http://127.0.0.1:8000`
2. Nhấn **"Đăng ký"** 
3. Nhập email và password
4. Nhấn **"Tạo tài khoản"**
5. **Quan trọng**: Check console output để thấy email verification link
6. Copy link và paste vào browser để verify email
7. Sau khi verify, login với email/password

### 3. Test Google OAuth:
1. Truy cập: `http://127.0.0.1:8000/accounts/login/`
2. Nhấn **"Đăng nhập với Google"** (nút đỏ)
3. Chọn tài khoản Google
4. Authorize app
5. Sẽ được redirect về dashboard

### 4. Test Features sau khi login:
- ✅ Dashboard hiển thị thống kê
- ✅ Thêm flashcard mới
- ✅ Xem danh sách flashcards
- ✅ User dropdown menu (email hiển thị)
- ✅ Logout functionality
- ✅ Language switching

## 📋 URL Routes để test:

```
http://127.0.0.1:8000/                    → Redirect to login
http://127.0.0.1:8000/accounts/login/     → Login page
http://127.0.0.1:8000/accounts/signup/    → Signup page
http://127.0.0.1:8000/dashboard/          → Dashboard (requires login)
http://127.0.0.1:8000/add/               → Add flashcard (requires login)
http://127.0.0.1:8000/flashcards/        → Flashcard list (requires login)
```

## 🔍 Kiểm tra trong Django Admin:

1. Truy cập: `http://127.0.0.1:8000/admin/`
2. Login với superuser (admin@test.com)
3. Kiểm tra:
   - **Users** → Custom users với email
   - **Social applications** → Google app
   - **Email addresses** → Verified emails
   - **Social accounts** → Google connected accounts

## 🎯 Expected Behavior:

### Anonymous users:
- Truy cập root `/` → redirect to login
- Truy cập protected URLs → redirect to login
- Chỉ thấy login/signup buttons

### Authenticated users:
- Truy cập root `/` → redirect to dashboard
- Thấy navigation menu đầy đủ
- Thấy user dropdown với email
- Chỉ thấy flashcards của mình
- Có thể logout

## 🐛 Troubleshooting:

### Google OAuth errors:
- Check redirect URIs trong Google Console
- Đảm bảo server chạy trên đúng port 8000
- Check console logs để debug

### Email verification:
- Email sẽ xuất hiện trong terminal console
- Copy toàn bộ URL từ "http://" đến hết
- Paste vào browser

### Database issues:
```bash
python manage.py flush  # Reset database nếu cần
python manage.py migrate
python manage.py createsuperuser --email admin@test.com
```

---

**🎉 Hệ thống Authentication đã sẵn sàng sử dụng!**

**Khuyến nghị test theo thứ tự:**
1. Email registration + verification
2. Login/logout với email
3. Google OAuth login
4. Add some flashcards
5. Test user isolation (tạo nhiều accounts) 