# 认证控制器 controller(登录/注册/退出)

# 通过Handler类展示 mvc 中的 controller 层如何接收表单，校验表单数据，调用模型层方法，再渲染视图 或 跳转
# 登录态用secure cookie 保存username
import tornado.web

from app.controllers.base import BaseHandler
from app.models.user import UserRepository


class LoginHandler(BaseHandler):
    # /auth/login
    # get: 渲染登录页
    # post: 校验用户名和密码,通过后写入secure cookie, 并跳转到目标页
    def get(self):
        self.render("login.html", title="登录", error=None)

    def post(self):
        username = (self.get_argument("username", "") or "").strip()
        password = self.get_argument("password", "")
        if not username or not password:
            self.set_status(400)
            return self.render(
                "login.html", title="登录", error="用户名或密码不能为空或输入了无效数据"
            )

        if not UserRepository.verify_user(username, password):
            self.set_status(401)
            return self.render("login.html", title="登录", error="用户名或密码错误")

        self.set_secure_cookie("username", username)
        self.redirect("/")


class LogoutHandler(BaseHandler):
    # /auth/logout
    def post(self):
        self.clear_cookie("username")
        self.redirect("/auth/login")


class RegisterHandler(BaseHandler):
    # /auth/register
    def get(self):
        self.render("register.html", title="注册", error=None, success=None)

    def post(self):
        username = (self.get_argument("username", "") or "").strip()
        password = self.get_argument("password", "")
        confirm_password = self.get_argument("confirm_password", "")

        if not username or not password or not confirm_password:
            self.set_status(400)
            return self.render(
                "register.html", title="注册", error="所有字段均为必填项", success=None
            )

        if len(username) < 2 or len(username) > 20:
            self.set_status(400)
            return self.render(
                "register.html", title="注册", error="用户名长度必须在2-20个字符之间", success=None
            )

        if len(password) < 6:
            self.set_status(400)
            return self.render(
                "register.html", title="注册", error="密码长度不能少于6位", success=None
            )

        if password != confirm_password:
            self.set_status(400)
            return self.render(
                "register.html", title="注册", error="两次输入的密码不一致", success=None
            )

        if UserRepository.create_user(username, password):
            self.render(
                "register.html",
                title="注册",
                error=None,
                success="注册成功，请登录",
            )
        else:
            self.render(
                "register.html", title="注册", error="用户名已存在", success=None
            )
