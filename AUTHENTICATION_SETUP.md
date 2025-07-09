# Hướng dẫn thiết lập Authentication

## 1. Cài đặt cơ bản đã hoàn thành ✅

### Những gì đã được triển khai:
- ✅ Custom User model với email authentication
- ✅ Email verification bắt buộc
- ✅ Login/Logout/Register templates đẹp
- ✅ @login_required cho tất cả views
- ✅ User-specific flashcards (mỗi user có dữ liệu riêng)
- ✅ Navigation với user dropdown
- ✅ Password reset functionality

## 2. Thiết lập Google OAuth (cần hoàn thành)

### Bước 1: Tạo Google OAuth App
1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project hiện có
3. Bật Google+ API
4. Tạo OAuth 2.0 credentials
5. Thêm authorized redirect URIs:
   - `http://127.0.0.1:8000/accounts/google/login/callback/`
   - `http://localhost:8000/accounts/google/login/callback/`

### Bước 2: Cập nhật settings.py
```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': 'your-actual-google-client-id',
            'secret': 'your-actual-google-client-secret',
        }
    }
}
```

### Bước 3: Thêm Social Application trong Django Admin
1. Chạy server: `python manage.py runserver`
2. Truy cập: `http://127.0.0.1:8000/admin/`
3. Vào **Social applications** → **Add social application**
4. Provider: **Google**
5. Name: **Google**
6. Client id: (từ Google Console)
7. Secret key: (từ Google Console)
8. Sites: Chọn **example.com**

## 3. Thiết lập Email (tuỳ chọn)

### Development (hiện tại):
Email sẽ hiển thị trong console khi chạy server.

### Production:
Cập nhật settings.py với Gmail SMTP:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-gmail@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Không phải password thường!
```

## 4. Test Authentication

1. **Đăng ký mới**: `/accounts/signup/`
2. **Đăng nhập email**: `/accounts/login/`
3. **Đăng nhập Google**: Nhấn nút "Sign in with Google"
4. **Logout**: User dropdown → Logout

## 5. Bảo mật

### Đã implement:
- ✅ Email verification bắt buộc
- ✅ User isolation (mỗi user chỉ thấy data của mình)
- ✅ CSRF protection
- ✅ Login required cho mọi views

### Khuyến nghị thêm:
- Rate limiting cho login attempts
- Strong password validation
- Two-factor authentication
- Session timeout

## 6. URL Routes

```
/accounts/login/          - Đăng nhập
/accounts/signup/         - Đăng ký
/accounts/logout/         - Đăng xuất
/accounts/password/reset/ - Quên mật khẩu
/accounts/email/          - Quản lý email
/accounts/google/login/   - Google OAuth
```

## 7. Troubleshooting

### Google OAuth không hoạt động:
- Kiểm tra client ID/secret
- Kiểm tra redirect URIs
- Kiểm tra Social Application trong admin

### Email verification không gửi:
- Kiểm tra console output (development)
- Kiểm tra email settings (production)
- Kiểm tra spam folder

### Lỗi migration:
```bash
python manage.py migrate --fake-initial
```

---

**Ghi chú**: Hệ thống authentication đã sẵn sàng sử dụng! Chỉ cần cài đặt Google OAuth credentials để hoàn thiện. 