import hashlib
import secrets

from app.models.db import get_connection


def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return dk.hex()


class RoleRepository:
    @staticmethod
    def create_role(
        name: str, code: str, description: str = "", is_system: int = 0
    ) -> int:
        with get_connection() as conn:
            exists = conn.execute(
                "select 1 from roles where code=? or name=?",
                (code, name),
            ).fetchone()
            if exists:
                raise ValueError("role exists")
            cursor = conn.execute(
                "insert into roles (name, code, description, is_system) values (?, ?, ?, ?)",
                (name, code, description, is_system),
            )
            return cursor.lastrowid

    @staticmethod
    def get_all_roles() -> list:
        with get_connection() as conn:
            return conn.execute(
                "select id, name, code, description, is_system, created_at from roles order by id"
            ).fetchall()

    @staticmethod
    def get_role(role_id: int):
        with get_connection() as conn:
            return conn.execute(
                "select id, name, code, description, is_system from roles where id=?",
                (role_id,),
            ).fetchone()

    @staticmethod
    def get_role_by_code(code: str):
        with get_connection() as conn:
            return conn.execute(
                "select id, name, code, description, is_system from roles where code=?",
                (code,),
            ).fetchone()

    @staticmethod
    def update_role(role_id: int, name: str, description: str) -> bool:
        with get_connection() as conn:
            is_sys = conn.execute(
                "select is_system from roles where id=?", (role_id,)
            ).fetchone()
            if is_sys and is_sys[0]:
                return False
            conn.execute(
                "update roles set name=?, description=? where id=?",
                (name, description, role_id),
            )
            return True

    @staticmethod
    def delete_role(role_id: int) -> bool:
        with get_connection() as conn:
            conn.execute("delete from role_permissions where role_id=?", (role_id,))
            conn.execute("update users set role_id=null where role_id=?", (role_id,))
            conn.execute("delete from user_roles where role_id=?", (role_id,))
            conn.execute("delete from roles where id=? and is_system=0", (role_id,))
            return True

    @staticmethod
    def get_permissions_by_role(role_id: int) -> list:
        with get_connection() as conn:
            return conn.execute(
                "select p.id, p.name, p.code, p.category from permissions p "
                "inner join role_permissions rp on p.id=rp.permission_id "
                "where rp.role_id=? order by p.category, p.id",
                (role_id,),
            ).fetchall()

    @staticmethod
    def set_role_permissions(role_id: int, permission_ids: list) -> bool:
        with get_connection() as conn:
            is_sys = conn.execute(
                "select code from roles where id=?", (role_id,)
            ).fetchone()
            if is_sys and is_sys[0] == "super_admin":
                return False
            conn.execute("delete from role_permissions where role_id=?", (role_id,))
            for pid in permission_ids:
                conn.execute(
                    "insert or ignore into role_permissions (role_id, permission_id) values (?, ?)",
                    (role_id, pid),
                )
            return True


class PermissionRepository:
    @staticmethod
    def create_permission(name: str, code: str, category: str = "") -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                "insert into permissions (name, code, category) values (?, ?, ?)",
                (name, code, category),
            )
            return cursor.lastrowid

    @staticmethod
    def get_all_permissions() -> list:
        with get_connection() as conn:
            return conn.execute(
                "select id, name, code, category from permissions order by category, id"
            ).fetchall()

    @staticmethod
    def get_permissions_by_category() -> dict:
        perms = PermissionRepository.get_all_permissions()
        result = {}
        for p in perms:
            cat = p["category"] or "其他"
            if cat not in result:
                result[cat] = []
            result[cat].append({"id": p["id"], "name": p["name"], "code": p["code"]})
        return result


class AdminUserRepository:
    @staticmethod
    def verify_admin(username: str, password: str):
        with get_connection() as conn:
            row = conn.execute(
                "select u.id, u.username, u.password_hash, u.salt, r.code as role_code "
                "from users u "
                "left join user_roles ur on u.id=ur.user_id "
                "left join roles r on ur.role_id=r.id "
                "where u.username=?",
                (username,),
            ).fetchone()
        if not row:
            return None
        salt = bytes.fromhex(row["salt"])
        if _hash_password(password, salt) != row["password_hash"]:
            return None
        return row

    @staticmethod
    def get_permissions_by_user_id(user_id: int) -> list:
        with get_connection() as conn:
            return conn.execute(
                "select distinct p.id, p.name, p.code, p.category "
                "from permissions p "
                "inner join role_permissions rp on p.id=rp.permission_id "
                "inner join users u on rp.role_id=u.role_id "
                "where u.id=? "
                "order by p.category, p.id",
                (user_id,),
            ).fetchall()

    @staticmethod
    def user_has_permission(user_id: int, permission_code: str) -> bool:
        with get_connection() as conn:
            row = conn.execute(
                "select 1 "
                "from permissions p "
                "inner join role_permissions rp on p.id=rp.permission_id "
                "inner join users u on rp.role_id=u.role_id "
                "where u.id=? and p.code=? "
                "limit 1",
                (user_id, permission_code),
            ).fetchone()
            if row:
                return True
            super_admin = conn.execute(
                "select 1 from users u join roles r on u.role_id=r.id where u.id=? and r.code='super_admin'",
                (user_id,),
            ).fetchone()
            return bool(super_admin)

    @staticmethod
    def get_admin_list(page: int = 1, page_size: int = 20, keyword: str = "") -> dict:
        offset = (page - 1) * page_size
        params = []
        where = ""
        if keyword:
            where = "where u.username like ?"
            params.append(f"%{keyword}%")

        with get_connection() as conn:
            total = conn.execute(
                f"select count(*) from users u {where}", params
            ).fetchone()[0]

            rows = conn.execute(
                f"""select u.id, u.username, u.created_at,
                   r.name as role_name,
                   r.code as role_code
                   from users u
                   left join roles r on u.role_id=r.id
                   {where}
                   order by u.id limit ? offset ?""",
                params + [page_size, offset],
            ).fetchall()

        result = []
        for row in rows:
            result.append(
                {
                    "id": row["id"],
                    "username": row["username"],
                    "role_names": row["role_name"] or "未分配",
                    "role_codes": row["role_code"] or "",
                    "created_at": row["created_at"],
                }
            )

        return {"total": total, "page": page, "page_size": page_size, "data": result}

    @staticmethod
    def create_admin_user(username: str, password: str) -> bool:
        salt = secrets.token_bytes(16)
        password_hash = _hash_password(password, salt)
        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    "insert into users (username, password_hash, salt) values (?, ?, ?)",
                    (username, password_hash, salt.hex()),
                )
                return cursor.lastrowid
        except Exception:
            return False

    @staticmethod
    def delete_admin_user(user_id: int) -> bool:
        with get_connection() as conn:
            is_sys = conn.execute(
                "select 1 from user_roles ur join roles r on ur.role_id=r.id "
                "where ur.user_id=? and r.code='super_admin'",
                (user_id,),
            ).fetchone()
            if is_sys:
                return False
            conn.execute("delete from user_roles where user_id=?", (user_id,))
            conn.execute("delete from conversations where user_id=?", (user_id,))
            conn.execute("delete from users where id=?", (user_id,))
            return True

    @staticmethod
    def update_admin_user(user_id: int, username: str) -> bool:
        try:
            with get_connection() as conn:
                is_sys = conn.execute(
                    "select 1 from user_roles ur join roles r on ur.role_id=r.id "
                    "where ur.user_id=? and r.code='super_admin'",
                    (user_id,),
                ).fetchone()
                if is_sys:
                    return False
                conn.execute(
                    "update users set username=? where id=?", (username, user_id)
                )
                return True
        except Exception:
            return False

    @staticmethod
    def update_admin_password(user_id: int, new_password: str) -> bool:
        salt = secrets.token_bytes(16)
        password_hash = _hash_password(new_password, salt)
        with get_connection() as conn:
            conn.execute(
                "update users set password_hash=?, salt=? where id=?",
                (password_hash, salt.hex(), user_id),
            )
            return True

    @staticmethod
    def set_user_role(user_id: int, role_id: int) -> bool:
        with get_connection() as conn:
            is_sys = conn.execute(
                "select 1 from users u join roles r on u.role_id=r.id where u.id=? and r.code='super_admin'",
                (user_id,),
            ).fetchone()
            if is_sys:
                return False
            exists = conn.execute("select 1 from roles where id=?", (role_id,)).fetchone()
            if not exists:
                return False
            conn.execute("update users set role_id=? where id=?", (role_id, user_id))
            conn.execute("delete from user_roles where user_id=?", (user_id,))
            conn.execute(
                "insert or ignore into user_roles (user_id, role_id) values (?, ?)",
                (user_id, role_id),
            )
            return True

    @staticmethod
    def set_user_roles(user_id: int, role_ids: list) -> bool:
        role_id = role_ids[0] if role_ids else None
        if role_id is None:
            return False
        return AdminUserRepository.set_user_role(user_id, int(role_id))

    @staticmethod
    def get_user_roles(user_id: int) -> list:
        with get_connection() as conn:
            row = conn.execute(
                "select r.id, r.name, r.code from users u left join roles r on u.role_id=r.id where u.id=?",
                (user_id,),
            ).fetchone()
            return [row] if row and row["id"] else []

    @staticmethod
    def is_super_admin(username: str) -> bool:
        with get_connection() as conn:
            row = conn.execute(
                """SELECT 1 FROM users u
                   JOIN user_roles ur ON u.id = ur.user_id
                   JOIN roles r ON ur.role_id = r.id
                   WHERE u.username = ? AND r.code = 'super_admin'""",
                (username,)
            ).fetchone()
            return row is not None
