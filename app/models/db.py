# 数据库链接与建表(ORM/DDL)
import os
import sqlite3


# 获得项目根路径的方法
def _project_root():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )


# 获取数据文件的路径
DB_PATH = os.path.join(_project_root(), "database", "app.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# 初始化数据库
def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at DATETIME DEFAULT(datetime('now','localtime'))
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL DEFAULT('新对话'),
                created_at DATETIME DEFAULT(datetime('now','localtime')),
                updated_at DATETIME DEFAULT(datetime('now','localtime')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT(datetime('now','localtime')),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """
        )

        conn.commit()
