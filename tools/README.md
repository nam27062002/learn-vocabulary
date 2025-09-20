# Database Sync Tool

Tool PyQt6 để đồng bộ hóa dữ liệu 2 chiều giữa PostgreSQL (server) và SQLite3 (local) cho ứng dụng Learn English.

## 🔧 Cài đặt

### 1. Cài đặt dependencies
```bash
cd D:\My Projects\Web\LearnEngish\tools
pip install -r requirements.txt
```

### 2. Chạy tool
```bash
python sync_gui.py
```

## 🎯 Tính năng

### ✅ **Giao diện trực quan**
- GUI PyQt6 thân thiện người dùng
- Hiển thị trạng thái kết nối real-time
- Progress bar cho quá trình sync
- Log chi tiết các hoạt động

### ✅ **Sync 2 chiều an toàn**
- **Server → Local**: Backup dữ liệu từ PostgreSQL về SQLite3
- **Local → Server**: Upload dữ liệu từ SQLite3 lên PostgreSQL
- **Clear toàn bộ**: Xóa hết data ở đích trước khi sync để đảm bảo 100% giống nhau

### ✅ **Quản lý bảng linh hoạt**
- Chọn bảng cần sync (Select All/Deselect)
- Hiển thị số lượng records từng bảng
- Sync chỉ những bảng được chọn

### ✅ **Bảo mật & kiểm tra**
- Test kết nối trước khi sync
- Confirmation dialog với cảnh báo rõ ràng
- Logging chi tiết mọi hoạt động
- Thread riêng để không block UI

## 📋 Danh sách bảng được sync

```
✓ auth_user
✓ auth_group
✓ auth_group_permissions
✓ auth_user_groups
✓ auth_user_user_permissions
✓ auth_permission
✓ django_content_type
✓ django_admin_log
✓ django_session
✓ django_migrations
✓ accounts_user
✓ vocabulary_deck
✓ vocabulary_flashcard
✓ vocabulary_definition
✓ vocabulary_studysession
✓ vocabulary_studysessionanswer
✓ vocabulary_dailystatistics
✓ vocabulary_weeklystatistics
✓ vocabulary_incorrectwordreview
✓ vocabulary_favoriteflashcard
✓ vocabulary_blacklistflashcard
```

## 🔐 Cấu hình Database

### Server (PostgreSQL)
```python
HOST: dpg-d2v8qv15pdvs73b5p5h0-a.oregon-postgres.render.com
DATABASE: learn_english_db_rjeh
USER: learn_english_db_rjeh_user
PASSWORD: rRmA7Z65LBtxIOW38q7Cpp1GxP9DZME8
PORT: 5432
```

### Local (SQLite3)
```python
PATH: D:\My Projects\Web\LearnEngish\db.sqlite3
```

## 🚨 Cảnh báo quan trọng

### ⚠️ **BACKUP TRƯỚC KHI SYNC**
- Tool này sẽ **XÓA TOÀN BỘ** dữ liệu ở đích
- Luôn backup trước khi chạy sync
- Không thể undo sau khi sync

### ⚠️ **Kiểm tra kết nối**
- Nhấn "Test Connections" trước khi sync
- Đảm bảo cả 2 database đều kết nối thành công

### ⚠️ **Chọn bảng cẩn thận**
- Chỉ sync những bảng cần thiết
- Tránh sync khi đang có user online (production)

## 📊 Hướng dẫn sử dụng

### 1. **Kiểm tra kết nối**
```
1. Mở tool → Nhấn "Test Connections"
2. Kiểm tra trạng thái: Server ✓ Connected, Local ✓ Connected
```

### 2. **Sync Server → Local (Backup)**
```
1. Chọn bảng cần backup
2. Nhấn "Server → Local"
3. Confirm trong dialog cảnh báo
4. Đợi quá trình hoàn tất
```

### 3. **Sync Local → Server (Upload)**
```
1. Chọn bảng cần upload
2. Nhấn "Local → Server"
3. Confirm trong dialog cảnh báo (NGUY HIỂM!)
4. Đợi quá trình hoàn tất
```

### 4. **Kiểm tra kết quả**
```
1. Nhấn "Refresh Table Info"
2. So sánh số lượng records Server vs Local
3. Check logs để xem chi tiết
```

## 🛠️ Cấu trúc file

```
tools/
├── database_config.py      # Cấu hình database
├── database_manager.py     # Logic kết nối & xử lý DB
├── sync_gui.py            # Giao diện PyQt6 chính
├── requirements.txt       # Dependencies
└── README.md             # Hướng dẫn này
```

## 🔧 Troubleshooting

### Lỗi kết nối PostgreSQL
```bash
# Kiểm tra firewall/network
ping dpg-d2v8qv15pdvs73b5p5h0-a.oregon-postgres.render.com

# Cài lại psycopg2
pip uninstall psycopg2-binary
pip install psycopg2-binary
```

### Lỗi SQLite
```bash
# Kiểm tra file tồn tại
ls "D:\My Projects\Web\LearnEngish\db.sqlite3"

# Chạy Django migrate nếu cần
cd "D:\My Projects\Web\LearnEngish"
python manage.py migrate
```

### Lỗi PyQt6
```bash
# Cài lại PyQt6
pip uninstall PyQt6
pip install PyQt6==6.7.1
```

## ⚡ Performance Tips

- **Sync theo batch**: Không sync tất cả bảng cùng lúc nếu data lớn
- **Thời điểm tối ưu**: Sync khi ít user online
- **Network**: Đảm bảo mạng ổn định cho PostgreSQL
- **Disk space**: Kiểm tra dung lượng ổ đĩa trước khi sync

---

**🎯 Mục đích**: Tool này được tạo để backup/restore dữ liệu an toàn cho ứng dụng Learn English, đảm bảo không mất data quan trọng.