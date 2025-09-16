# Fresh Database Migration Tools

## 🎯 Mục đích
Đảm bảo dữ liệu giữa source database và target database **100% giống nhau** bằng cách xóa hoàn toàn target database trước khi migrate.

## 🛠️ Tools đã tạo

### 1. `clear_database.py` - Database Clearing Tool
**Chức năng**: Xóa toàn bộ dữ liệu trong target database
```bash
python tools/clear_database.py
```
- Hiển thị tổng quan dữ liệu hiện tại  
- Yêu cầu confirm bằng cách gõ `DELETE ALL`
- Xóa toàn bộ dữ liệu và reset sequences
- Verify database đã hoàn toàn trống

### 2. `complete_fresh_migration.py` - Complete Fresh Migration
**Chức năng**: Quy trình migration hoàn chỉnh với 3 bước
```bash
python tools/complete_fresh_migration.py
```

**Quy trình:**
1. **Clear Target Database**: Xóa hoàn toàn target database
2. **Fresh Migration**: Copy toàn bộ dữ liệu từ source
3. **Data Verification**: Kiểm tra consistency 100%

**Yêu cầu confirm**: Gõ `FRESH MIGRATION` để xác nhận

### 3. `migration_gui.py` - Enhanced GUI
**Chức năng**: GUI với tính năng auto-clear
- ✅ Checkbox: "Clear target database before migration (ensures 100% consistency)"
- ✅ Real-time progress tracking
- ✅ Background processing

### 4. Batch Files
- `run_fresh_migration.bat` - Chạy complete fresh migration
- `run_migration_gui.bat` - Chạy enhanced GUI

## 🚀 Cách sử dụng

### Option 1: Complete Fresh Migration (Command Line)
```bash
# Automatic: Clear + Migrate + Verify
python tools/complete_fresh_migration.py
```

### Option 2: Enhanced GUI
```bash
# GUI với auto-clear option
python tools/migration_gui.py
```

### Option 3: Manual Steps  
```bash
# Bước 1: Clear database
python tools/clear_database.py

# Bước 2: Migrate data
python tools/auto_migrate.py
```

## ⚡ Tính năng mới

### 🔄 Auto-Clear Process
- **Disable foreign keys**: `SET session_replication_role = replica`
- **Clear all tables**: `DELETE FROM` cho tất cả bảng
- **Reset sequences**: `ALTER SEQUENCE ... RESTART WITH 1`
- **Re-enable foreign keys**: `SET session_replication_role = DEFAULT`

### 📊 Data Verification
- So sánh row count giữa source và target
- Báo cáo chi tiết inconsistencies
- Xác nhận 100% data consistency

### 🛡️ Safety Features
- Multiple confirmation prompts
- Connection testing trước khi bắt đầu
- Atomic operations (all-or-nothing)
- Detailed error reporting

## 📋 Kết quả mong đợi

**Trước migration:**
- Source DB: 7,708 rows
- Target DB: có thể có dữ liệu cũ/không đồng bộ

**Sau fresh migration:**
- Source DB: 7,708 rows  
- Target DB: 7,708 rows (100% identical)
- ✅ Zero inconsistencies
- ✅ All sequences properly reset

## 🎯 Khi nào sử dụng Fresh Migration?

✅ **Nên sử dụng khi:**
- Cần đảm bảo dữ liệu 100% consistency
- Target database có dữ liệu cũ/corrupt
- Thực hiện migration lần đầu
- Muốn "clean slate" cho target database

⚠️ **Cẩn thận khi:**
- Target database có dữ liệu quan trọng
- Đang trong production environment
- Chưa có backup

## 🔧 Troubleshooting

**Lỗi foreign key violations:**
- Fresh migration tool tự động disable/enable foreign keys
- Đảm bảo proper sequence trong migration

**Connection errors:**
- Check database credentials
- Verify network connectivity  
- Ensure databases are accessible

**Permission errors:**
- User cần quyền DELETE, INSERT, ALTER SEQUENCE
- Check database user permissions