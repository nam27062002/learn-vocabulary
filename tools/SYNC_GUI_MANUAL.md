# Database Sync GUI - User Manual

## 🚀 Quick Start Guide

### 1. Launch Application
```bash
cd "D:\My Projects\Web\LearnEngish\tools"
python sync_gui.py
```

### 2. Configure Databases (New Feature!)
Click **🔧 Configure Databases** to open configuration dialog:

#### **PostgreSQL Server Tab**
- Host: Your PostgreSQL server address
- Port: Usually 5432
- Database: Your main database name
- Username/Password: Your credentials

#### **Local Database Tab**
- **SQLite**: Select for local SQLite file (default: `db.sqlite3`)
- **PostgreSQL**: Select for local PostgreSQL server

#### **Target PostgreSQL Server Tab** (New!)
- **Pre-configured** with Render.com PostgreSQL server
- Default: `learn_english_db_wuep` on Oregon server
- **Ready to use** for PostgreSQL→PostgreSQL sync
- Can be customized for other target servers

### 3. Choose Sync Destination (New Feature!)
Select from dropdown **🎯 Sync Destination**:

- **PostgreSQL → SQLite (Local)**: Standard sync to local SQLite
- **SQLite → PostgreSQL (Server)**: Upload local data to server
- **PostgreSQL → PostgreSQL (Server)**: Advanced server-to-server sync

### 4. Test Connections
Click **🔌 Test Connections** to verify all database connections.

### 5. Discover & Select Tables
1. Click **🔍 Discover Tables** to load available tables
2. Use search box to filter tables
3. Select tables you want to sync

### 6. Perform Sync
- **📥 Server → Local**: Download from server to local
- **📤 Local → Server**: Upload from local to server

## 🔄 PostgreSQL to PostgreSQL Sync (New!)

### Setup
1. Configure **PostgreSQL Server** (source)
2. Configure **Target PostgreSQL Server** (destination)
3. Select **PostgreSQL → PostgreSQL (Server)** from destination dropdown

### Sync Options
- **📥 Source Server → Target Server**: Copy from source to target
- **📤 Target Server → Source Server**: Copy from target to source

### Features
- ✅ **Batch Processing**: Handles large tables efficiently (100 rows/batch)
- ✅ **Transaction Safety**: Commits after each batch
- ✅ **Error Recovery**: Continues with next table if one fails
- ✅ **Progress Tracking**: Real-time progress updates

## 🛠️ Advanced Features

### Keyboard Shortcuts
- **F11** or **Alt+Enter**: Toggle fullscreen
- **Ctrl+T**: Test connections
- **Ctrl+D**: Discover tables
- **Ctrl+R**: Refresh table info
- **Ctrl+F**: Focus search box
- **Esc**: Close dialogs

### Safety Features
- **Confirmation dialogs** before destructive operations
- **Access Violation protection** via multiprocessing
- **Connection validation** before sync
- **Error logging** with timestamps

### Performance Optimizations
- **Chunked processing** for large datasets
- **Memory management** with garbage collection
- **Non-blocking UI** during sync operations
- **Connection pooling** for efficiency

## 🔧 Configuration Tips

### For SQLite Local
- Path: `db.sqlite3` (default)
- Automatic creation if doesn't exist
- No additional setup required

### For PostgreSQL Local
- Same machine as GUI application
- Different port if needed (e.g., 5433)
- Separate credentials if required

### For Target PostgreSQL Server
- **Pre-configured**: Render.com PostgreSQL (`learn_english_db_wuep`)
- **Production ready**: Oregon-based server with SSL
- **Same schema structure** as source database
- **Cloud accessible** from any location

## ⚡ Sync Modes Explained

| Mode | Source | Destination | Use Case |
|------|--------|-------------|----------|
| PG→SQLite | PostgreSQL Server | SQLite Local | Development, Backup |
| SQLite→PG | SQLite Local | PostgreSQL Server | Deploy, Upload |
| PG→PG | PostgreSQL Server | PostgreSQL Target | Migration, Replication |

## 🚨 Important Notes

1. **Backup first**: Always backup before sync operations
2. **Schema compatibility**: Ensure target has same table structure
3. **Network stability**: Stable connection required for large syncs
4. **Permissions**: Ensure database user has required permissions
5. **Transaction size**: Large tables are processed in batches

## 🐛 Troubleshooting

### Common Issues
- **Connection failed**: Check host, port, credentials
- **Permission denied**: Verify database user permissions
- **Table not found**: Ensure schema exists in target
- **Memory issues**: Sync fewer tables at once

### Error Recovery
- Check log panel for detailed error messages
- Try syncing individual tables to isolate issues
- Verify network connectivity for server syncs
- Restart application if needed

## 📊 Monitoring

### Progress Tracking
- **Progress bar**: Overall completion percentage
- **Status messages**: Current operation details
- **Log panel**: Detailed operation history
- **Error reporting**: Clear error messages with timestamps

### Performance Metrics
- Tables processed count
- Records transferred
- Time elapsed
- Memory usage (when available)

---

**Version**: Enhanced with PostgreSQL-to-PostgreSQL sync
**Last Updated**: December 2024
**Author**: Database Sync Tool Team