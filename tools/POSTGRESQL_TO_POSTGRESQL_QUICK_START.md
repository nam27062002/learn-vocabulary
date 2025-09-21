# PostgreSQL to PostgreSQL Sync - Quick Start

## 🚀 5-Minute Setup Guide

### Step 1: Launch Application
```bash
cd "D:\My Projects\Web\LearnEngish\tools"
python sync_gui.py
```

### Step 2: Verify Target Server (Pre-configured!)
The target server is **already configured** with Render.com PostgreSQL:
- **Host**: `dpg-d32033juibrs739dn540-a.oregon-postgres.render.com`
- **Database**: `learn_english_db_wuep`
- **User**: `learn_english_db_wuep_user`
- **Ready to use** immediately!

### Step 3: Select PostgreSQL→PostgreSQL Mode
1. In **🎯 Sync Destination** dropdown
2. Select: **"PostgreSQL → PostgreSQL (Server)"**
3. Buttons will update to show server-to-server options

### Step 4: Test Connections
Click **🔌 Test Connections** to verify:
- ✅ Source PostgreSQL server
- ✅ Target PostgreSQL server (Render.com)

### Step 5: Discover & Select Tables
1. Click **🔍 Discover Tables**
2. Select tables you want to sync
3. Use search filter if needed

### Step 6: Perform Sync
- **📥 Source Server → Target Server**: Copy from local server to Render.com
- **📤 Target Server → Source Server**: Copy from Render.com to local server

## ⚙️ Advanced Configuration

### Custom Target Server
If you want to use a different target server:

1. Click **🔧 Configure Databases**
2. Go to **"Target PostgreSQL Server"** tab
3. Update connection details
4. Click **"Test Connections"** to verify
5. Click **"Apply"** to save

### Sync Modes Available

| Mode | Direction | Use Case |
|------|-----------|----------|
| Source → Target | Local → Render.com | Deploy/Backup to cloud |
| Target → Source | Render.com → Local | Download/Restore from cloud |

## 🔐 Security Features

- **SSL/TLS encryption** for Render.com connections
- **Automatic SSL detection** for `.render.com` hosts
- **Secure credential storage** during session
- **Connection validation** before sync

## 📊 Performance Features

- **Batch processing**: 100 rows per batch for large tables
- **Progress tracking**: Real-time progress updates
- **Error recovery**: Continues with next table if one fails
- **Memory management**: Automatic cleanup between tables

## 🛠️ Troubleshooting

### Connection Issues
```bash
# Test target server separately
python test_render_connection.py
```

### Common Solutions
- **Timeout errors**: Check internet connection
- **SSL errors**: Ensure firewall allows HTTPS/SSL
- **Permission errors**: Verify database user permissions
- **Memory issues**: Sync fewer tables at once

## 💡 Best Practices

1. **Always backup** before syncing
2. **Test with small tables** first
3. **Monitor progress** in log panel
4. **Use consistent schema** between servers
5. **Check table counts** after sync

## 🎯 Example Workflow

### Deploy to Production (Source → Target)
```
1. Select "PostgreSQL → PostgreSQL (Server)"
2. Test connections
3. Select deployment tables (e.g., vocabulary, accounts)
4. Click "📥 Source Server → Target Server"
5. Monitor progress in log panel
6. Verify data in target server
```

### Backup from Production (Target → Source)
```
1. Select "PostgreSQL → PostgreSQL (Server)"
2. Test connections
3. Select all production tables
4. Click "📤 Target Server → Source Server"
5. Monitor progress in log panel
6. Verify local backup
```

## 🚨 Important Notes

- **Schema compatibility**: Ensure both servers have same table structure
- **Data conflicts**: Target tables are cleared before sync
- **Transaction safety**: Each batch commits separately
- **Network dependency**: Stable internet required for cloud sync

---

**Target Server**: `learn_english_db_wuep` on Render.com Oregon
**SSL Enabled**: Automatic for `.render.com` hosts
**Batch Size**: 100 rows (optimized for performance)
**Timeout**: 10 seconds per connection