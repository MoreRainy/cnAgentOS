import json
import urllib.error
import urllib.request

import tornado.web
import tornado.gen
import tornado.ioloop

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

    async def prepare(self):
        # The login page itself does not need authentication or role checks
        if self.request.path == "/admin/login":
            return

        # If not logged in, the @authenticated decorator will redirect
        if not self.current_user:
            return

        # Check if the user is a super admin
        if not AdminUserRepository.is_super_admin(self.current_user):
            # For API requests, return a JSON error
            if 'api' in self.request.path:
                self.set_status(403)
                self.write({"code": 403, "msg": "无权访问"})
                self.finish()
            # For page requests, render the no_access page
            else:
                self.render("admin/no_access.html")
                self.finish()


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
                role_id = body.get("role_id")
                if role_id:
                    AdminUserRepository.set_user_role(uid, int(role_id))
                self.write({"code": 0, "msg": "添加成功"})
            else:
                self.write({"code": -1, "msg": "用户名已存在"})

        elif action == "update":
            if AdminUserRepository.update_admin_user(body["id"], body["username"]):
                role_id = body.get("role_id")
                if role_id is not None:
                    AdminUserRepository.set_user_role(body["id"], int(role_id))
                self.write({"code": 0, "msg": "修改成功"})
            else:
                self.write({"code": -1, "msg": "修改失败：无法修改超级管理员或用户名已存在。"})

        elif action == "delete":
            if AdminUserRepository.delete_admin_user(body["id"]):
                self.write({"code": 0, "msg": "删除成功"})
            else:
                self.write({"code": -1, "msg": "操作失败：无法删除超级管理员。"})

        elif action == "batch_delete":
            ids = body.get("ids", [])
            success_count = 0
            fail_count = 0
            for uid in ids:
                if AdminUserRepository.delete_admin_user(uid):
                    success_count += 1
                else:
                    fail_count += 1
            msg = f"成功删除 {success_count} 个用户。"
            if fail_count > 0:
                msg += f" {fail_count} 个用户（如超级管理员）无法删除。"
            self.write({"code": 0, "msg": msg})

        elif action == "reset_password":
            AdminUserRepository.update_admin_password(body["id"], body["password"])
            self.write({"code": 0, "msg": "密码重置成功"})

        elif action == "set_roles":
            role_id = body.get("role_id")
            if role_id is None:
                self.write({"code": -1, "msg": "请选择一个角色"})
            elif AdminUserRepository.set_user_role(body["id"], int(role_id)):
                self.write({"code": 0, "msg": "角色设置成功"})
            else:
                self.write({"code": -1, "msg": "无法为超级管理员设置角色或角色不存在。"})

        else:
            self.write({"code": -1, "msg": "未知操作"})


class AdminRoleApiHandler(AdminBaseHandler):
    @tornado.web.authenticated
    def get(self):
        action = self.get_argument("action", "")
        if action == "all":
            if not self.has_permission("role:view"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
            roles = RoleRepository.get_all_roles()
            self.write({"code": 0, "data": [dict(r) for r in roles]})
            return

        role_id = self.get_argument("role_id", None)
        if role_id:
            if not self.has_permission("role:view"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
            perms = RoleRepository.get_permissions_by_role(int(role_id))
            self.write({"code": 0, "data": [dict(p) for p in perms]})
            return

        if not self.has_permission("role:view"):
            self.set_status(403)
            self.write({"code": -1, "msg": "无权限执行该操作"})
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
            if not self.has_permission("role:add"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
            try:
                RoleRepository.create_role(
                    body["name"], body["code"], body.get("description", ""), 0
                )
                self.write({"code": 0, "msg": "添加成功"})
            except ValueError:
                self.write({"code": -1, "msg": "角色编码或名称已存在"})
        elif action == "update":
            if not self.has_permission("role:edit"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
            if RoleRepository.update_role(
                body["id"], body["name"], body.get("description", "")
            ):
                self.write({"code": 0, "msg": "更新成功"})
            else:
                self.write({"code": -1, "msg": "无法修改系统角色"})
        elif action == "delete":
            if not self.has_permission("role:delete"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
            if RoleRepository.delete_role(body["id"]):
                self.write({"code": 0, "msg": "删除成功"})
            else:
                self.write({"code": -1, "msg": "无法删除系统角色"})
        elif action == "set_permissions":
            if not self.has_permission("role:edit"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
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
        if not self.has_permission("perm:view"):
            self.set_status(403)
            self.write({"code": -1, "msg": "无权限执行该操作"})
            return
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
            if not self.has_permission("perm:add"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
            PermissionRepository.create_permission(
                body["name"], body["code"], body.get("category", "")
            )
            self.write({"code": 0, "msg": "添加成功"})
        elif action == "update":
            if not self.has_permission("perm:edit"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
            with get_connection() as conn:
                conn.execute(
                    "update permissions set name=?, code=?, category=? where id=?",
                    (body["name"], body["code"], body.get("category", ""), body["id"]),
                )
            self.write({"code": 0, "msg": "更新成功"})
        elif action == "delete":
            if not self.has_permission("perm:delete"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
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

        if not self.has_permission("menu:view"):
            self.set_status(403)
            self.write({"code": -1, "msg": "无权限执行该操作"})
            return
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
            if not self.has_permission("menu:add"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
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
            if not self.has_permission("menu:edit"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
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
            if not self.has_permission("menu:delete"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
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
            if not self.has_permission("model:add"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
            model_id = ModelEngineRepository.create_model(
                body["name"],
                body["model_name"],
                body["base_url"],
                body["api_key"],
                body.get("is_default", 0),
            )
            self.write({"code": 0, "msg": "添加成功", "id": model_id})
        elif action == "update":
            if not self.has_permission("model:edit"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
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
            if not self.has_permission("model:delete"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
            ModelEngineRepository.delete_model(body["id"])
            self.write({"code": 0, "msg": "删除成功"})
        elif action == "set_default":
            if not self.has_permission("model:edit"):
                self.set_status(403)
                self.write({"code": -1, "msg": "无权限执行该操作"})
                return
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

        if not self.has_permission("model:test"):
            self.write(f"data: {json.dumps({'error': '无权限执行该操作'})}\n\n")
            await self.flush()
            return

        def _stream_error(message: str):
            self.write(f"data: {json.dumps({'error': message}, ensure_ascii=False)}\n\n")

        api_key = (model_info["api_key"] or "").strip()
        base_url = (model_info["base_url"] or "").strip().rstrip("/")
        model_name = (model_info["model_name"] or "").strip()

        if not api_key or not base_url or not model_name:
            _stream_error("模型配置不完整，请检查 API Key、Base URL 和模型标识")
            await self.flush()
            return

        if base_url.endswith("/v1"):
            chat_url = f"{base_url}/chat/completions"
        else:
            chat_url = f"{base_url}/v1/chat/completions"

        payload = json.dumps(
            {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
            },
            ensure_ascii=False,
        ).encode("utf-8")

        request = urllib.request.Request(
            chat_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        tokens = 0
        full_answer = ""
        try:
            loop = tornado.ioloop.IOLoop.current()
            response = await loop.run_in_executor(None, lambda: urllib.request.urlopen(request, timeout=120))

            with response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="ignore").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except Exception:
                        continue

                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content") or ""
                    if content:
                        full_answer += content
                        tokens += len(content)
                        self.write(f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n")
                        await self.flush()

            if full_answer:
                ModelEngineRepository.increment_token_count(model_id, max(1, tokens // 2))
            self.write("data: [DONE]\n\n")
            await self.flush()

        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else ""
            message = f"模型接口请求失败({e.code})"
            if detail:
                message = f"{message}: {detail[:200]}"
            _stream_error(message)
            await self.flush()
        except Exception as e:
            _stream_error(f"AI 对话失败：{str(e)}")
            await self.flush()
