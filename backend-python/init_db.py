from app.database import init_db


if __name__ == "__main__":
    init_db(seed=True)
    print("数据库初始化完成：backend-python/data/dream_archive.db")

