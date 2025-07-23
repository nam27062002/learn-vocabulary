# Dropdown Menu Mutual Exclusion Fix

## Vấn đề
Trong navigation bar, có hai dropdown buttons: "Change Language" và "Profile". Khi click vào dropdown "Change Language" và sau đó click vào dropdown "Profile", cả hai dropdown menu đều mở và chồng lấp lên nhau, tạo ra xung đột về giao diện.

## Giải pháp
Đã implement logic mutual exclusion để đảm bảo chỉ có một dropdown được mở tại một thời điểm.

### Các thay đổi chính:

#### 1. File `static/js/main.js`
- Thêm mảng `dropdownMenus` để theo dõi tất cả dropdown menus
- Sửa đổi hàm `setupDropdown` để thêm logic mutual exclusion
- Khi một dropdown được mở, tất cả dropdown khác sẽ tự động đóng
- Cập nhật xử lý phím Escape để sử dụng mảng `dropdownMenus`

#### 2. File `staticfiles/js/main.js`
- Áp dụng cùng logic như `static/js/main.js`
- Đảm bảo tính nhất quán giữa các file

#### 3. File `templates/account/base.html`
- Cập nhật script language switcher để sử dụng logic mutual exclusion
- Thêm xử lý phím Escape cho account pages

### Logic hoạt động:

1. **Mở dropdown**: Khi click vào một dropdown, tất cả dropdown khác sẽ đóng trước, sau đó dropdown được click sẽ toggle (mở/đóng)

2. **Click outside**: Khi click bên ngoài dropdown, dropdown sẽ đóng

3. **Phím Escape**: Khi nhấn phím Escape, tất cả dropdown sẽ đóng

4. **Mobile menu**: Khi mở mobile menu, tất cả dropdown sẽ đóng

### Cách test:

1. Mở file `test_dropdown.html` trong browser
2. Click vào "🌐 Language" dropdown - nó sẽ mở
3. Click vào "👤 Profile" dropdown - Language dropdown sẽ đóng, Profile dropdown sẽ mở
4. Click lại vào "🌐 Language" - Profile dropdown sẽ đóng, Language dropdown sẽ mở
5. Click bên ngoài cả hai dropdown - cả hai sẽ đóng
6. Nhấn phím Escape - cả hai sẽ đóng

### Files đã được sửa đổi:
- `static/js/main.js`
- `staticfiles/js/main.js` 
- `templates/account/base.html`
- `test_dropdown.html` (file test)

### Lệnh đã chạy:
```bash
python manage.py collectstatic --noinput
```

## Kết quả
- ✅ Chỉ có một dropdown mở tại một thời điểm
- ✅ Click vào dropdown khác sẽ đóng dropdown hiện tại
- ✅ Click bên ngoài sẽ đóng tất cả dropdown
- ✅ Phím Escape sẽ đóng tất cả dropdown
- ✅ Không còn tình trạng chồng lấp dropdown 