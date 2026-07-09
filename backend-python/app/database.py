import hashlib
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "dream_archive.db"


def get_conn():
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def password_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _ensure_schema_migrations(conn: sqlite3.Connection):
    # Backward compatible migration for old sqlite files.
    cols = [row[1] for row in conn.execute("PRAGMA table_info(dream_records)").fetchall()]
    if "anonymous_name" not in cols:
        conn.execute("ALTER TABLE dream_records ADD COLUMN anonymous_name TEXT")
    if "deleted_by_admin" not in cols:
        conn.execute("ALTER TABLE dream_records ADD COLUMN deleted_by_admin INTEGER NOT NULL DEFAULT 0")
    if "updated_at" not in cols:
        conn.execute("ALTER TABLE dream_records ADD COLUMN updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP")


def init_db(seed: bool = False):
    with get_conn() as conn:
        _ensure_schema_migrations(conn)
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              password_hash TEXT NOT NULL,
              role TEXT NOT NULL DEFAULT 'USER',
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS dream_records (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              title TEXT NOT NULL,
              content TEXT NOT NULL,
              dream_date TEXT NOT NULL,
              mood_score INTEGER NOT NULL,
              is_public INTEGER NOT NULL DEFAULT 0,
              audit_status TEXT NOT NULL DEFAULT 'PRIVATE',
              anonymous_name TEXT,
              deleted_by_admin INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS dream_symbols (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              keyword TEXT NOT NULL UNIQUE,
              category TEXT NOT NULL,
              fun_explanation TEXT NOT NULL,
              psychology_explanation TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS dream_analyses (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              dream_id INTEGER NOT NULL,
              matched_keywords TEXT,
              rule_based_result TEXT,
              ai_result TEXT,
              risk_level TEXT NOT NULL DEFAULT 'LOW',
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(dream_id) REFERENCES dream_records(id)
            );

            CREATE TABLE IF NOT EXISTS sensitive_words (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              word TEXT NOT NULL UNIQUE,
              level TEXT NOT NULL DEFAULT 'HIGH'
            );

            CREATE TABLE IF NOT EXISTS dream_comments (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              dream_id INTEGER NOT NULL,
              user_id INTEGER NOT NULL,
              content TEXT NOT NULL,
              is_deleted INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(dream_id) REFERENCES dream_records(id),
              FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS dream_likes (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              dream_id INTEGER NOT NULL,
              user_id INTEGER NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(dream_id, user_id),
              FOREIGN KEY(dream_id) REFERENCES dream_records(id),
              FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )
        if seed:
            seed_db(conn)


def seed_db(conn: sqlite3.Connection):
    conn.execute(
        "INSERT OR IGNORE INTO users(username, password_hash, role) VALUES (?, ?, ?)",
        ("alice", password_hash("123456"), "USER"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO users(username, password_hash, role) VALUES (?, ?, ?)",
        ("admin", password_hash("admin123"), "ADMIN"),
    )

    symbols = [
        ("考试", "压力", "像是正在被某件事考验。", "可能和评价焦虑、任务压力有关。"),
        ("学校", "场景", "学校常代表成长、规则和回忆。", "可能与学习压力或过去经历有关。"),
        ("坠落", "动作", "像是突然失去掌控。", "可能和不安全感、失控感有关。"),
        ("追逐", "动作", "像是在逃离某个压力源。", "可能与现实压力或未解决问题有关。"),
        ("水", "意象", "水常和情绪流动有关。", "可能反映情绪波动。"),
        ("故人", "角色", "故人出现常带有怀念或未说完的话。", "可能和记忆、依恋或遗憾有关。"),
        ("迷路", "场景", "迷路像是在寻找方向。", "可能与选择困难或目标模糊有关。"),
        ("飞翔", "动作", "飞翔常带来自由感。", "可能与释放压力或渴望突破有关。"),
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO dream_symbols
        (keyword, category, fun_explanation, psychology_explanation)
        VALUES (?, ?, ?, ?)
        """,
        symbols,
    )

    words = [("自伤", "HIGH"), ("自杀", "HIGH"), ("杀人", "HIGH"), ("暴力", "HIGH"), ("违法", "HIGH")]
    conn.executemany("INSERT OR IGNORE INTO sensitive_words(word, level) VALUES (?, ?)", words)

    alice = conn.execute("SELECT id FROM users WHERE username = 'alice'").fetchone()
    if alice:
        conn.execute(
            """
            INSERT OR IGNORE INTO dream_records
            (id, user_id, title, content, dream_date, mood_score, is_public, audit_status, anonymous_name)
            VALUES (1, ?, ?, ?, ?, ?, 1, 'PUBLISHED', '梦游者1001')
            """,
            (
                alice["id"],
                "找不到教室的考试",
                "我梦见自己在学校考试，但是一直找不到教室，后来又从楼梯上坠落。",
                "2026-07-07",
                2,
            ),
        )
