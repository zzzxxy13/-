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
    cols = [row[1] for row in conn.execute("PRAGMA table_info(dream_records)").fetchall()]
    if "anonymous_name" not in cols:
        conn.execute("ALTER TABLE dream_records ADD COLUMN anonymous_name TEXT")
    if "deleted_by_admin" not in cols:
        conn.execute("ALTER TABLE dream_records ADD COLUMN deleted_by_admin INTEGER NOT NULL DEFAULT 0")
    if "updated_at" not in cols:
        conn.execute("ALTER TABLE dream_records ADD COLUMN updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP")
    if "is_public" not in cols:
        conn.execute("ALTER TABLE dream_records ADD COLUMN is_public INTEGER NOT NULL DEFAULT 0")
    if "audit_status" not in cols:
        conn.execute("ALTER TABLE dream_records ADD COLUMN audit_status TEXT NOT NULL DEFAULT 'PRIVATE'")

    comment_cols = [row[1] for row in conn.execute("PRAGMA table_info(dream_comments)").fetchall()]
    if comment_cols and "is_deleted" not in comment_cols:
        conn.execute("ALTER TABLE dream_comments ADD COLUMN is_deleted INTEGER NOT NULL DEFAULT 0")


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
        ("飞翔|飞行|翅膀", "关系", "想摆脱压力、恢复掌控感。", "常见于突破约束、对自由的渴望。"),
        ("坠落|掉下|摔下", "行动", "失控和安全感断裂的核心意象。", "常与焦虑、恐惧或缺乏掌控感相关。"),
        ("追逐|被追|追赶", "行动", "回避、逃离或被时间追赶。", "映照现实里“赶不上节奏”的压力体验。"),
        ("考试|答辩|面试", "价值评估", "对自我表现和结果的高度关注。", "常对应“我是否够好”“是否会被否定”的担忧。"),
        ("迟到|超时|迟缓", "价值评估", "对时间压力和评价场景的再现。", "建议关注现实中是否存在持续“赶不上的任务”信号。"),
        ("校园|教室|老家|家|教室", "场景", "熟悉场景出现新的变形。", "说明旧经验正在与当前现实问题叠加。"),
        ("深海|湖泊|洪水|淹没|水|大海", "意象", "情绪吞没感与边界模糊。", "常提示精力被任务或关系占满，需分离重点。"),
        ("发光|光柱|星光|月光", "意象", "短暂安全感、清晰线索。", "常是大脑给出的舒缓锚点，可用于日后记录中的安心片段。"),
        ("流血|受伤|出血|擦伤", "身体", "高唤醒状态下的警觉表达。", "多数为压力象征，不等同于真实身体疾病。"),
        ("火|燃烧|爆炸|烟|烟雾", "情绪", "积累情绪的突发释放。", "可与压抑、委屈、突发冲突后的心理张力相关。"),
        ("迷路|找不到路|陌生路|失去方向", "关系", "方向感受损、认知疲惫。", "建议任务分解，降低一次性决策负担。"),
        ("陌生人|模糊面孔|看不清", "社会", "边界不确定与警觉。", "常见于对陌生环境或新关系的试探。"),
        ("猫|狗|动物|鸟|鱼", "替代角色", "本能与直觉被“动物化”承载。", "说明情绪可能转化为更安全的表达载体。"),
        ("黑暗|阴影|废墟|阴森", "场景", "不确定感和未被理解体验。", "可先写下“最害怕的结果”再做呼吸放松。"),
        ("水底|溺水|窒息", "身体", "强烈窒息或恐慌线索。", "提示睡前放松呼吸与减少信息输入。"),
        ("高空|悬崖|跳跃|飞起|坠落", "情境", "边界试探与冒险幻想并存。", "可理解为变化/风险想象训练，不必神化处理。"),
        ("发芽|植物|花朵|树", "场景", "成长、修复与更新意象。", "常见于经历调整后对自我复元的期待。"),
        ("火车|地铁|公交|车站", "场景", "过渡与转换感受。", "通常对应“身份迁移/阶段切换”焦虑。"),
        ("迟迟入睡|失眠|醒来", "情境", "睡眠节律被打乱。", "可与现实作息、压力和咖啡因相关，先排查睡前流程。"),
        ("雨|雷电|风暴|暴风", "情绪", "内在波动和外界扰动同步。", "可先把“强度最高的片段”独立复盘。"),
        ("镜子|影子|倒影", "意象", "自我认知的反射过程。", "常提示“我是否听见了另一个自己”的提问。"),
        ("老年|老人|父母|家人", "关系", "亲密关系投射或责任感被激活。", "关注现实照顾关系带来的负荷。"),
        ("追梦|重生|重置|回到过去", "时间错位", "时间感被重排。", "提醒你关注是否存在未完成事件在心理上重播。"),
        ("门|钥匙|锁|钥匙孔", "关系", "进出边界和可达性场景。", "可作为“该允许什么/暂不允许什么”的心理隐喻。"),
        ("楼梯|地窖|隧道", "场景", "转折点、过渡阶段感受。", "常与任务负荷上升或身份跃迁有关。"),
    ]

    conn.executemany(
        """
        INSERT OR IGNORE INTO dream_symbols
        (keyword, category, fun_explanation, psychology_explanation)
        VALUES (?, ?, ?, ?)
        """,
        symbols,
    )

    words = [
        ("自残", "HIGH"),
        ("自杀", "HIGH"),
        ("他伤", "HIGH"),
        ("自我伤害", "HIGH"),
        ("严重暴力", "HIGH"),
    ]
    conn.executemany("INSERT OR IGNORE INTO sensitive_words(word, level) VALUES (?, ?)", words)

    alice = conn.execute("SELECT id FROM users WHERE username = 'alice'").fetchone()
    if alice:
        conn.execute(
            """
            INSERT OR IGNORE INTO dream_records
            (id, user_id, title, content, dream_date, mood_score, is_public, audit_status, anonymous_name)
            VALUES (1, ?, ?, ?, ?, ?, 1, 'PUBLISHED', '梦者001')
            """,
            (
                alice["id"],
                "考试反复梦的夜晚",
                "我在旧校园里迟到，来不及答题，后来飞起来又坠落。",
                "2026-07-07",
                2,
            ),
        )


def _safe_table_columns(conn: sqlite3.Connection, table_name: str):
    try:
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    except sqlite3.OperationalError:
        return None
    return [row[1] for row in rows]


def _ensure_schema_migrations_compat(conn: sqlite3.Connection):
    cols = _safe_table_columns(conn, "dream_records")
    if cols:
        if "anonymous_name" not in cols:
            conn.execute("ALTER TABLE dream_records ADD COLUMN anonymous_name TEXT")
        if "deleted_by_admin" not in cols:
            conn.execute("ALTER TABLE dream_records ADD COLUMN deleted_by_admin INTEGER NOT NULL DEFAULT 0")
        if "updated_at" not in cols:
            conn.execute("ALTER TABLE dream_records ADD COLUMN updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP")
        if "is_public" not in cols:
            conn.execute("ALTER TABLE dream_records ADD COLUMN is_public INTEGER NOT NULL DEFAULT 0")
        if "audit_status" not in cols:
            conn.execute("ALTER TABLE dream_records ADD COLUMN audit_status TEXT NOT NULL DEFAULT 'PRIVATE'")

    comment_cols = _safe_table_columns(conn, "dream_comments")
    if comment_cols and "is_deleted" not in comment_cols:
        conn.execute("ALTER TABLE dream_comments ADD COLUMN is_deleted INTEGER NOT NULL DEFAULT 0")


def _init_tables_if_missing(conn: sqlite3.Connection):
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


def init_db(seed: bool = False):
    with get_conn() as conn:
        _init_tables_if_missing(conn)
        _ensure_schema_migrations_compat(conn)
        if seed:
            seed_db(conn)
