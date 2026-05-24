import json
import tornado.web
import tornado.gen

from app.models.db import get_connection
from app.controllers.base import BaseHandler
from app.models.admin import (
    AdminUserRepository,
    RoleRepository,
    PermissionRepository,
)
from app.models.model_engine import ModelEngineRepository


class AdminLoginHandler(BaseHandler):
    def get(self):
        self.render("admin_login.html", title="后台登录", error=None)

    def post(self):
        username = (self.get_argument("username", "") or "").strip()
        password = self.get_argument("password", "")
        if not username or not password:
            return self.render(
                "admin_login.html", title="后台登录", error="用户名或密码不能为空"
            )

        row = AdminUserRepository.verify_admin(username, password)
        if not row:
            return self.render(
                "admin_login.html", title="后台登录", error="用户名或密码错误"
            )

        self.set_secure_cookie("admin_user", username)
        self.redirect("/admin")


class AdminLogoutHandler(BaseHandler):
    def post(self):
        self.clear_cookie("admin_user")
        self.redirect("/admin/login")


class AdminBaseHandler(BaseHandler):
    def get_current_user(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            return None
        return username.decode("utf-8")


class AdminIndexHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        menus = self._get_menus()
        self.render(
            "admin/index.html",
            title="管理后台",
            username=self.current_user,
            menus=menus,
        )

    def _get_menus(self):
        from app.models.db import get_connection

        with get_connection() as conn:
            rows = conn.execute(
                "select id, name, icon, url, parent_id, sort_order from menus where is_visible=1 order by sort_order, id"
            ).fetchall()
        return [dict(r) for r in rows]


class AdminUserPageHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/users.html", title="用户管理", username=self.current_user)


class AdminMenuPageHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/menus.html", title="功能管理", username=self.current_user)


class AdminRolePageHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("admin/roles.html", title="角色管理", username=self.current_user)


class AdminPermPageHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render(
            "admin/permissions.html", title="权限管理", username=self.current_user
        )


class AdminPlaceholderHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self, module_name):
        pages = {
            "roles": {
                "title": "角色管理",
                "icon": "layui-icon-group",
                "add": "角色",
            },
            "permissions": {
                "title": "权限管理",
                "icon": "layui-icon-auz",
                "add": "权限",
            },
            "menus": {"title": "功能管理", "icon": "layui-icon-app", "add": "菜单"},
        }
        info = pages.get(
            module_name,
            {"title": "页面不存在", "icon": "layui-icon-face-surprised", "add": ""},
        )
        self.render(
            "admin/placeholder.html",
            page_title=info["title"],
            icon_class=info["icon"],
            add_label=info["add"],
        )


class AdminModelPageHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        per_page = 6
        models, total = ModelEngineRepository.get_all_models(page, per_page)
        total_pages = (total + per_page - 1) // per_page
        self.render(
            "admin/models.html",
            title="模型引擎",
            username=self.current_user,
            models=[dict(m) for m in models],
            current_page=page,
            total_pages=total_pages,
            total_records=total,
        )


class AdminUserApiHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        limit = int(self.get_argument("limit", 20))
        keyword = self.get_argument("keyword", "")
        result = AdminUserRepository.get_admin_list(page, limit, keyword)
        result["code"] = 0
        result["msg"] = ""
        self.write(result)

    @tornado.web.authenticated
    def post(self):
        body = json.loads(self.request.body)
        action = body.get("action")
        if action == "add":
            uid = AdminUserRepository.create_admin_user(
                body["username"], body["password"]
            )
            if uid:
                role_ids = body.get("role_ids", [])
                if role_ids:
                    AdminUserRepository.set_user_roles(uid, role_ids)
                self.write({"code": 0, "msg": "添加成功"})
            else:
                self.write({"code": -1, "msg": "用户名已存在"})
        elif action == "update":
            if AdminUserRepository.update_admin_user(body["id"], body["username"]):
                role_ids = body.get("role_ids")
                if role_ids is not None:
                    AdminUserRepository.set_user_roles(body["id"], role_ids)
                self.write({"code": 0, "msg": "修改成功"})
            else:
                self.write(
                    {
                        "code": -1,
                        "msg": "修改失败，可能用户名已存在或为系统管理员",
                    }
                )
        elif action == "delete":
            if AdminUserRepository.delete_admin_user(body["id"]):
                self.write({"code": 0, "msg": "删除成功"})
            else:
                self.write({"code": -1, "msg": "无法删除系统管理员"})
        elif action == "batch_delete":
            ids = body.get("ids", [])
            success = 0
            for uid in ids:
                if AdminUserRepository.delete_admin_user(uid):
                    success += 1
            self.write({"code": 0, "msg": f"成功删除 {success} 个用户"})
        elif action == "reset_password":
            AdminUserRepository.update_admin_password(body["id"], body["password"])
            self.write({"code": 0, "msg": "密码重置成功"})
        elif action == "set_roles":
            if AdminUserRepository.set_user_roles(body["id"], body.get("role_ids", [])):
                self.write({"code": 0, "msg": "角色设置成功"})
            else:
                self.write({"code": -1, "msg": "无法为系统管理员设置角色"})
        else:
            self.write({"code": -1, "msg": "未知操作"})


class AdminRoleApiHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        action = self.get_argument("action", "")
        if action == "all":
            roles = RoleRepository.get_all_roles()
            self.write({"code": 0, "data": [dict(r) for r in roles]})
            return

        role_id = self.get_argument("role_id", None)
        if role_id:
            perms = RoleRepository.get_permissions_by_role(int(role_id))
            self.write({"code": 0, "data": [dict(p) for p in perms]})
            return

        all_perms = PermissionRepository.get_permissions_by_category()
        roles = RoleRepository.get_all_roles()
        self.write(
            {"code": 0, "data": {"roles": [dict(r) for r in roles], "perms": all_perms}}
        )

    @tornado.web.authenticated
    def post(self):
        body = json.loads(self.request.body)
        action = body.get("action")
        if action == "add":
            RoleRepository.create_role(
                body["name"], body["code"], body.get("description", ""), 0
            )
            self.write({"code": 0, "msg": "添加成功"})
        elif action == "update":
            if RoleRepository.update_role(
                body["id"], body["name"], body.get("description", "")
            ):
                self.write({"code": 0, "msg": "更新成功"})
            else:
                self.write({"code": -1, "msg": "无法修改系统角色"})
        elif action == "delete":
            if RoleRepository.delete_role(body["id"]):
                self.write({"code": 0, "msg": "删除成功"})
            else:
                self.write({"code": -1, "msg": "无法删除系统角色"})
        elif action == "set_permissions":
            if RoleRepository.set_role_permissions(
                body["id"], body.get("permission_ids", [])
            ):
                self.write({"code": 0, "msg": "权限设置成功"})
            else:
                self.write({"code": -1, "msg": "无法修改超级管理员权限"})


class AdminPermApiHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        action = self.get_argument("action", "")
        if action == "all":
            perms = PermissionRepository.get_all_permissions()
            self.write({"code": 0, "data": [dict(p) for p in perms]})
        else:
            perms = PermissionRepository.get_permissions_by_category()
            self.write({"code": 0, "data": perms})

    @tornado.web.authenticated
    def post(self):
        body = json.loads(self.request.body)
        action = body.get("action")
        if action == "add":
            PermissionRepository.create_permission(
                body["name"], body["code"], body.get("category", "")
            )
            self.write({"code": 0, "msg": "添加成功"})
        elif action == "update":
            with get_connection() as conn:
                conn.execute(
                    "update permissions set name=?, code=?, category=? where id=?",
                    (body["name"], body["code"], body.get("category", ""), body["id"]),
                )
            self.write({"code": 0, "msg": "更新成功"})
        elif action == "delete":
            with get_connection() as conn:
                conn.execute(
                    "delete from role_permissions where permission_id=?", (body["id"],)
                )
                conn.execute("delete from permissions where id=?", (body["id"],))
            self.write({"code": 0, "msg": "删除成功"})


class AdminMenuApiHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        from app.models.db import get_connection

        with get_connection() as conn:
            rows = conn.execute(
                "select id, name, icon, url, parent_id, sort_order, is_visible from menus order by sort_order, id"
            ).fetchall()
        self.write({"code": 0, "data": [dict(r) for r in rows]})

    @tornado.web.authenticated
    def post(self):
        from app.models.db import get_connection

        body = json.loads(self.request.body)
        action = body.get("action")
        if action == "add":
            with get_connection() as conn:
                conn.execute(
                    "insert into menus (name, icon, url, parent_id, sort_order, is_visible) values (?,?,?,?,?,?)",
                    (
                        body["name"],
                        body.get("icon", ""),
                        body.get("url", ""),
                        body.get("parent_id", 0),
                        body.get("sort_order", 0),
                        body.get("is_visible", 1),
                    ),
                )
            self.write({"code": 0, "msg": "添加成功"})
        elif action == "update":
            with get_connection() as conn:
                conn.execute(
                    "update menus set name=?, icon=?, url=?, parent_id=?, sort_order=?, is_visible=? where id=?",
                    (
                        body["name"],
                        body.get("icon", ""),
                        body.get("url", ""),
                        body.get("parent_id", 0),
                        body.get("sort_order", 0),
                        body.get("is_visible", 1),
                        body["id"],
                    ),
                )
            self.write({"code": 0, "msg": "更新成功"})
        elif action == "delete":
            with get_connection() as conn:
                conn.execute("delete from menus where id=?", (body["id"],))
            self.write({"code": 0, "msg": "删除成功"})


class AdminModelApiHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        per_page = int(self.get_argument("limit", 6))
        models, total = ModelEngineRepository.get_all_models(page, per_page)
        self.write(
            {
                "code": 0,
                "msg": "",
                "count": total,
                "data": [dict(m) for m in models],
            }
        )

    @tornado.web.authenticated
    def post(self):
        body = json.loads(self.request.body)
        action = body.get("action")
        if action == "add":
            model_id = ModelEngineRepository.create_model(
                body["name"],
                body["model_name"],
                body["base_url"],
                body["api_key"],
                body.get("is_default", 0),
            )
            self.write({"code": 0, "msg": "添加成功", "id": model_id})
        elif action == "update":
            ModelEngineRepository.update_model(
                body["id"],
                body["name"],
                body["model_name"],
                body["base_url"],
                body["api_key"],
                body.get("is_default", 0),
            )
            self.write({"code": 0, "msg": "更新成功"})
        elif action == "delete":
            ModelEngineRepository.delete_model(body["id"])
            self.write({"code": 0, "msg": "删除成功"})
        elif action == "set_default":
            ModelEngineRepository.set_default_model(body["id"])
            self.write({"code": 0, "msg": "设置默认成功"})
        else:
            self.write({"code": -1, "msg": "未知操作"})


class AdminModelTestApiHandler(AdminBaseHandler):
    @tornado.web.authenticated
    async def post(self):
        self.set_header("Content-Type", "text/event-stream; charset=utf-8")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Connection", "keep-alive")
        self.set_header("X-Accel-Buffering", "no")

        body = json.loads(self.request.body or b"{}")
        model_id = body.get("id") or self.get_argument("id", None)
        prompt = body.get("prompt", "") or self.get_argument("prompt", "")

        model_info = ModelEngineRepository.get_model_by_id(model_id)
        if not model_info:
            self.write(f"data: {json.dumps({'error': 'Model not found'})}\n\n")
            await self.flush()
            return

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=model_info["api_key"], base_url=model_info["base_url"]
            )
            stream = await client.chat.completions.create(
                model=model_info["model_name"],
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            tokens = 0
            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    content = getattr(delta, "content", "") or ""
                    if content:
                        tokens += len(content)
                        self.write(f"data: {json.dumps({'content': content})}\n\n")
                        await self.flush()

            ModelEngineRepository.increment_token_count(model_id, max(1, tokens // 2))
            self.write("data: [DONE]\n\n")
            await self.flush()

        except Exception as e:
            self.write(f"data: {json.dumps({'error': str(e)})}\n\n")
            await self.flush()
