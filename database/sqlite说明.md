# 数据库说明

Python 版 MVP 默认使用 SQLite，数据库文件运行后自动生成：

```text
backend-python/data/dream_archive.db
```

初始化命令：

```bash
cd backend-python
python init_db.py
```

SQLite 文件属于运行数据，不上传 GitHub，已经写入 `.gitignore`。

如后续需要改成 MySQL，可以保留当前表结构，把 `app/database.py` 中的 sqlite3 访问替换为 SQLAlchemy 或 MySQL 驱动。

