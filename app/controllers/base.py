# Controller 公共基础类(BaseController)
"""
在tornado中
    - 每一个URL对应一个RequestHandler类 可以理解为Controller
    - 每一个RequestHandler类都有一个get()方法,用于处理GET请求
    - 每一个RequestHandler类都有一个post()方法,用于处理POST请求

本程序可以提供一个统一的基础类,用于处理一些公共业务,比如登录态的处理或获得逻辑,供其他Controller继承。
"""

import tornado.web

from app.models.admin import AdminUserRepository
from app.models.user import UserRepository


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        username = self.get_secure_cookie("username")
        if not username:
            return None
        return username.decode("utf-8")

    def get_current_admin_user(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            return None
        return username.decode("utf-8")

    def get_user_permissions(self, username: str) -> set[str]:
        user = UserRepository.get_user_by_username(username)
        if not user:
            return set()
        perms = AdminUserRepository.get_permissions_by_user_id(user["id"])
        return {p["code"] for p in perms}

    def get_user_id(self):
        username = self.get_current_user() or self.get_current_admin_user()
        if not username:
            return None
        user = UserRepository.get_user_by_username(username)
        return user["id"] if user else None

    def has_permission(self, code: str) -> bool:
        user_id = self.get_user_id()
        if not user_id:
            return False
        return AdminUserRepository.user_has_permission(user_id, code)

    def deny_permission(self, required_permission: str | None = None):
        accept = self.request.headers.get("Accept", "")
        if self.request.path.startswith("/admin/api/") or "application/json" in accept:
            self.set_status(403)
            self.write({"code": -1, "msg": "无权限执行该操作"})
            return
        self.render(
            "admin/forbidden.html",
            title="无权限访问",
            required_permission=required_permission,
        )
