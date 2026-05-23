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

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                code TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT(''),
                is_system INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT(datetime('now','localtime'))
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT(datetime('now','localtime')),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (role_id) REFERENCES roles(id),
                UNIQUE(user_id, role_id)
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT NOT NULL UNIQUE,
                category TEXT DEFAULT(''),
                created_at DATETIME DEFAULT(datetime('now','localtime'))
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS role_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                FOREIGN KEY (role_id) REFERENCES roles(id),
                FOREIGN KEY (permission_id) REFERENCES permissions(id),
                UNIQUE(role_id, permission_id)
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS menus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                icon TEXT DEFAULT(''),
                url TEXT DEFAULT(''),
                parent_id INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                is_visible INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT(datetime('now','localtime'))
            )
        """
        )

        conn.commit()


def seed_admin_data():
    import hashlib
    import secrets

    with get_connection() as conn:
        existing = conn.execute(
            "select 1 from roles where code='super_admin'"
        ).fetchone()
        if not existing:
            conn.execute(
                "insert into roles (name, code, description, is_system) values (?, ?, ?, ?)",
                ("超级管理员", "super_admin", "系统内置超级管理员", 1),
            )
            conn.execute(
                "insert into roles (name, code, description, is_system) values (?, ?, ?, ?)",
                ("普通管理员", "admin", "普通管理员角色", 0),
            )
            admin_exist = conn.execute(
                "select 1 from users where username='admin'"
            ).fetchone()
            if not admin_exist:
                password = "admin888"
                salt = secrets.token_bytes(16)
                dk = hashlib.pbkdf2_hmac(
                    "sha256", password.encode("utf-8"), salt, 100000
                )
                password_hash = dk.hex()
                cursor = conn.execute(
                    "insert into users (username, password_hash, salt) values (?, ?, ?)",
                    ("admin", password_hash, salt.hex()),
                )
                user_id = cursor.lastrowid
                conn.execute(
                    "insert into user_roles (user_id, role_id) values (?, ?)",
                    (user_id, 1),
                )

        existing_perms = conn.execute("select 1 from permissions limit 1").fetchone()
        if not existing_perms:
            perms = [
                ("查看用户", "user:view", "用户管理"),
                ("新增用户", "user:add", "用户管理"),
                ("编辑用户", "user:edit", "用户管理"),
                ("删除用户", "user:delete", "用户管理"),
                ("查看角色", "role:view", "角色管理"),
                ("新增角色", "role:add", "角色管理"),
                ("编辑角色", "role:edit", "角色管理"),
                ("删除角色", "role:delete", "角色管理"),
                ("查看权限", "perm:view", "权限管理"),
                ("新增权限", "perm:add", "权限管理"),
                ("删除权限", "perm:delete", "权限管理"),
                ("查看菜单", "menu:view", "功能管理"),
                ("新增菜单", "menu:add", "功能管理"),
                ("编辑菜单", "menu:edit", "功能管理"),
                ("删除菜单", "menu:delete", "功能管理"),
                ("查看模型", "model:view", "模型引擎"),
                ("新增模型", "model:add", "模型引擎"),
                ("编辑模型", "model:edit", "模型引擎"),
                ("删除模型", "model:delete", "模型引擎"),
                ("模型测试", "model:test", "模型引擎"),
            ]
            for name, code, cat in perms:
                conn.execute(
                    "insert into permissions (name, code, category) values (?, ?, ?)",
                    (name, code, cat),
                )

        existing_menus = conn.execute("select 1 from menus limit 1").fetchone()
        if not existing_menus:
            menus = [
                ("用户管理", "layui-icon-user", "/admin/users", 0, 1),
                ("角色管理", "layui-icon-group", "/admin/roles", 0, 2),
                ("权限管理", "layui-icon-auz", "/admin/permissions", 0, 3),
                ("功能管理", "layui-icon-app", "/admin/menus", 0, 4),
                ("模型引擎", "layui-icon-engine", "/admin/models", 0, 5),
            ]
            for name, icon, url, pid, sort in menus:
                conn.execute(
                    "insert into menus (name, icon, url, parent_id, sort_order) values (?, ?, ?, ?, ?)",
                    (name, icon, url, pid, sort),
                )

        super_role = conn.execute(
            "select id from roles where code='super_admin'"
        ).fetchone()
        if super_role:
            perm_count = conn.execute(
                "select count(*) from role_permissions where role_id=?",
                (super_role["id"],),
            ).fetchone()[0]
            if perm_count == 0:
                all_perms = conn.execute("select id from permissions").fetchall()
                for p in all_perms:
                    conn.execute(
                        "insert or ignore into role_permissions (role_id, permission_id) values (?, ?)",
                        (super_role["id"], p["id"]),
                    )

        conn.commit()
