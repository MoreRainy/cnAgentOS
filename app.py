# 程序的主入口
# 承担服务器容器+程序作用
# 服务器容器：提供http容器服务，程序放置于该容器中运行
# 程序：本体-智能瞭望与智能问数系统 B/S架构

import os
from tornado import autoreload
import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer

from app.controllers.base import BaseHandler
from app.controllers.auth import LogoutHandler, RegisterHandler
from app.controllers.home import IndexHandler
from app.controllers.chat import (
    ChatHandler,
    ChatApiHandler,
    ChatSendHandler,
    ChatDetailHandler,
    ChatDeleteHandler,
)
from app.controllers.auth import LoginHandler
from app.controllers.admin import (
    AdminLoginHandler,
    AdminLogoutHandler,
    AdminIndexHandler,
    AdminUserPageHandler,
    AdminPlaceholderHandler,
    AdminUserApiHandler,
    AdminRoleApiHandler,
    AdminPermApiHandler,
    AdminMenuApiHandler,
)
from app.models.db import init_db, seed_admin_data


def make_app():
    base_url = os.path.dirname(os.path.abspath(__file__))
    settings = dict(
        # 预留view层的内容配置
        template_path=os.path.join(base_url, "app", "templates"),  # 模板路径
        static_path=os.path.join(base_url, "app", "static"),  # 静态文件路径
        debug=True,  # 开启调试模式, 会打印日志
        cookie_secret="123456",  # 加密cookie的密钥
        login_url="/auth/login",  # 登录页的URL
        xsrf_cookies=True,  # 开启xsrf保护
        autoreload=True,  # 开启自动重新加载
    )
    return tornado.web.Application(
        [
            (r"/auth/login", LoginHandler),
            (r"/auth/logout", LogoutHandler),
            (r"/auth/register", RegisterHandler),
            (r"/chat", ChatHandler),
            (r"/chat/api", ChatApiHandler),
            (r"/chat/api/send", ChatSendHandler),
            (r"/chat/api/(\d+)", ChatDetailHandler),
            (r"/chat/api/(\d+)/delete", ChatDeleteHandler),
            (r"/admin/login", AdminLoginHandler),
            (r"/admin/logout", AdminLogoutHandler),
            (r"/admin", AdminIndexHandler),
            (r"/admin/users", AdminUserPageHandler),
            (r"/admin/api/users", AdminUserApiHandler),
            (r"/admin/api/roles", AdminRoleApiHandler),
            (r"/admin/api/permissions", AdminPermApiHandler),
            (r"/admin/api/menus", AdminMenuApiHandler),
            (r"/admin/(\w+)", AdminPlaceholderHandler),
            (r"/", IndexHandler),
        ],
        **settings,
    )


if __name__ == "__main__":
    init_db()
    seed_admin_data()
    app = make_app()
    server = HTTPServer(app)
    server.bind(10086)
    # 自动cpu核心数
    server.start()

    print("=============server started============= 端口:10086======", flush=True)
    tornado.ioloop.IOLoop.current().start()
