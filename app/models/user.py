import hashlib
import secrets
import sqlite3

from app.models.db import get_connection


DEFAULT_ROLE_CODE = "user"


# 密码加密方法
def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return dk.hex()


# 用户对象类
class UserRepository:
    # 创建用户的方法
    # 返回值：True/False
    @staticmethod
    def create_user(username: str, password: str) -> bool:
        salt = secrets.token_bytes(16)
        password_hash = _hash_password(password, salt)

        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    "insert into users (username,password_hash,salt) values (?,?,?)",
                    (username, password_hash, salt.hex()),
                )
                user_id = cursor.lastrowid

                role_row = conn.execute(
                    "select id from roles where code=?",
                    (DEFAULT_ROLE_CODE,),
                ).fetchone()
                if role_row:
                    conn.execute(
                        "insert or ignore into user_roles (user_id, role_id) values (?, ?)",
                        (user_id, role_row["id"]),
                    )
            return True
        except sqlite3.IntegrityError:
            return False

    # 根据用户名查询用户的方法
    # 返回值：用户对象或None
    @staticmethod
    def get_user_by_username(username: str):
        with get_connection() as conn:
            row = conn.execute(
                "select id,username,password_hash,salt from users where username=?",
                (username,),
            ).fetchone()
            return row

    # 验证用户密码的方法
    # 返回值：True/False
    @staticmethod
    def verify_user(username: str, password: str) -> bool:
        row = UserRepository.get_user_by_username(username)
        if row is None:
            return False

        salt = bytes.fromhex(row["salt"])
        return _hash_password(password, salt) == row["password_hash"]
