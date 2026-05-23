# cnAgentOS - AI智能瞭望与智能问数系统

> 基于 Tornado 6.5.5 + SQLite + Python 3.12 构建的 B/S 架构智能问数系统

---

## 项目概述

cnAgentOS 是一个 AI 智能瞭望与智能问数系统，采用 B/S（浏览器/服务器）架构。系统基于 Python 3.12 和 Tornado 6.5.5 框架构建，数据存储采用 SQLite 轻量级数据库，前端使用原生 HTML + CSS + JavaScript。

**项目当前状态**：已完成基础 MVC 架构搭建和用户登录验证功能。

---

## 技术栈

| 层级 | 技术 | 版本/说明 |
|------|------|-----------|
| **后端框架** | Tornado | 6.5.5 - 异步非阻塞 Web 框架 |
| **编程语言** | Python | 3.12 |
| **数据库** | SQLite | 内置轻量级关系型数据库 |
| **前端模板** | Tornado Template | 内置模板引擎 |
| **前端 UI 框架** | Layui | 2.13.6（本地化部署） |
| **前端 CSS 框架** | Bootstrap | 5.3.8（本地化部署） |
| **前端图标库** | FontAwesome | 5.15.4（本地化部署） |
| **前端技术** | HTML + CSS + JavaScript | 原生实现 |
| **加密方式** | PBKDF2-HMAC-SHA256 | 密码哈希，100000 次迭代 |

> **注意**：所有前端组件均已本地化部署，不引用任何互联网资源。组件存放于 `app/static/dist/` 目录下。
>
> **组件引用路径**（Tornado static_url）：
> - Layui: `{{ static_url('dist/layui/css/layui.css') }}` / `{{ static_url('dist/layui/layui.js') }}`
> - Bootstrap: `{{ static_url('dist/bootstrap-5.3.8-dist/css/bootstrap.min.css') }}` / `{{ static_url('dist/bootstrap-5.3.8-dist/js/bootstrap.bundle.min.js') }}`
> - FontAwesome: `{{ static_url('dist/fontawesome-free-5.15.4-web/css/all.min.css') }}`

---

## 项目架构

### 整体架构：MVC 模式

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端浏览器                              │
│                    (HTML + CSS + JS)                             │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP 请求/响应
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Tornado HTTP Server                          │
│                      (端口: 10086)                               │
└──────────────────────────────┬──────────────────────────────────┘
                               │ 路由分发
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Controller 层 (控制器)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  BaseHandler │  │ AuthHandler  │  │    IndexHandler      │   │
│  │ (基础认证)    │  │ (登录/登出)   │  │   (后台首页)          │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │ 调用
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Model 层 (模型)                            │
│  ┌──────────────────────────────┐  ┌────────────────────────┐   │
│  │        db.py (数据库)         │  │  user.py (用户模型)     │   │
│  │ - 连接管理                    │  │ - 用户注册              │   │
│  │ - 表初始化                    │  │ - 用户查询              │   │
│  │ - 路径解析                    │  │ - 密码验证              │   │
│  └──────────────────────────────┘  └────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │ SQL 操作
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SQLite Database (app.db)                     │
│                     ┌──────────────────────┐                    │
│                     │      users 表         │                    │
│                     │ - id (PK)            │                    │
│                     │ - username (UNIQUE)  │                    │
│                     │ - password_hash      │                    │
│                     │ - salt               │                    │
│                     │ - created_at         │                    │
│                     └──────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### 目录结构

```
cnAgentOS/
├── app.py                          # 程序主入口（HTTP容器 + 应用实例）
├── README.md                       # 项目架构与技术栈说明
├── requirement.md                  # 需求开发跟踪文档（人类与AI共同维护）
├── app/
│   ├── __init__.py                 # Python 包标识
│   ├── controllers/                # Controller 层（控制器）
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseHandler - 基础控制器（认证逻辑）
│   │   ├── auth.py                 # AuthHandler - 认证控制器（登录/登出）
│   │   └── home.py                 # IndexHandler - 首页控制器
│   ├── models/                     # Model 层（数据模型）
│   │   ├── __init__.py
│   │   ├── db.py                   # 数据库连接与初始化
│   │   └── user.py                 # 用户模型与仓储（UserRepository）
│   ├── templates/                  # View 层（模板视图）
│   │   ├── base.html               # 基础模板（布局框架）
│   │   ├── login.html              # 登录页面
│   │   ├── register.html           # 注册页面（已预留，待实现）
│   │   └── index.html              # 后台首页（登录后）
│   └── static/                     # 静态资源
│       ├── css/
│       │   └── base.css            # 基础样式表
│       ├── js/
│       │   └── base.js             # 基础脚本
│       └── dist/                   # 第三方前端组件（本地化部署）
│           ├── layui/              # Layui 2.13.6（待配置）
│           ├── bootstrap-5.3.8-dist/  # Bootstrap 5.3.8
│           │   ├── css/            # Bootstrap CSS 文件
│           │   └── js/             # Bootstrap JS 文件
│           └── fontawesome-free-5.15.4-web/  # FontAwesome 5.15.4
│               ├── css/            # FontAwesome CSS 文件
│               ├── js/             # FontAwesome JS 文件
│               ├── webfonts/       # 字体文件
│               └── svgs/           # SVG 图标
├── database/
│   └── app.db                      # SQLite 数据库文件
└── test.py                         # 用户模块单元测试脚本
```

---

## 已实现功能

### 1. 用户登录认证

**功能说明**：用户通过输入用户名和密码登录系统，系统验证通过后写入 Secure Cookie 并跳转至后台页面。

**实现流程**：
```
用户访问 /auth/login → LoginHandler.get() 渲染登录页
用户提交表单 → LoginHandler.post() 验证用户 → UserRepository.verify_user()
  → 验证成功 → 写入 Secure Cookie → 重定向到 /
  → 验证失败 → 显示错误信息，保持登录页
```

**关键代码**：
- [LoginHandler](file:///c:/Users/HuTao/Desktop/school/20260516/WorkSpace/Day4/cnAgentOS/app/controllers/auth.py#L11-L33) - 处理登录请求
- [UserRepository.verify_user()](file:///c:/Users/HuTao/Desktop/school/20260516/WorkSpace/Day4/cnAgentOS/app/models/user.py#L44-L51) - 密码验证逻辑

### 2. 用户登出功能

**功能说明**：用户点击退出按钮，清除 Secure Cookie 并重定向到登录页面。

**实现流程**：
```
用户提交登出表单 → LogoutHandler.post() → 清除 Cookie → 重定向到 /auth/login
```

**关键代码**：
- [LogoutHandler](file:///c:/Users/HuTao/Desktop/school/20260516/WorkSpace/Day4/cnAgentOS/app/controllers/auth.py#L36-L39) - 处理登出请求

### 3. 登录态保护

**功能说明**：使用 Tornado 的 `@tornado.web.authenticated` 装饰器实现未登录用户自动跳转登录页。

**实现机制**：
```
BaseHandler.get_current_user() 读取 Secure Cookie 中的 username
  → 返回 username 字符串 → 用户已登录
  → 返回 None → 未登录 → 自动跳转到 login_url (/login.jsp)
```

**关键代码**：
- [BaseHandler.get_current_user()](file:///c:/Users/HuTao/Desktop/school/20260516/WorkSpace/Day4/cnAgentOS/app/controllers/base.py#L18-L23) - 获取当前登录用户
- [IndexHandler](file:///c:/Users/HuTao/Desktop/school/20260516/WorkSpace/Day4/cnAgentOS/app/controllers/home.py#L5-L8) - 使用 @tornado.web.authenticated 装饰器保护后台页面

### 4. 用户注册（API层）

**功能说明**：提供用户注册的数据层接口，支持密码 PBKDF2 哈希加密存储。

**关键代码**：
- [UserRepository.create_user()](file:///c:/Users/HuTao/Desktop/school/20260516/WorkSpace/Day4/cnAgentOS/app/models/user.py#L19-L31) - 创建用户（已实现 Model 层，待实现 Controller 和 View 层）

### 5. 安全防护

| 安全机制 | 实现方式 |
|----------|----------|
| **密码加密** | PBKDF2-HMAC-SHA256，10 万次迭代，随机 salt |
| **Secure Cookie** | 使用 cookie_secret 加密，防止伪造 |
| **XSRF 保护** | 开启 xsrf_cookies，表单包含 `{% module xsrf_form_html() %}` |

---

## 核心模块说明

### Controller 层（控制器）

#### BaseHandler - 基础控制器
- **位置**：[app/controllers/base.py](file:///c:/Users/HuTao/Desktop/school/20260516/WorkSpace/Day4/cnAgentOS/app/controllers/base.py)
- **职责**：
  - 继承 `tornado.web.RequestHandler`
  - 实现 `get_current_user()` 方法，用于登录态判断
  - 作为其他 Handler 的公共父类

#### AuthHandler - 认证控制器
- **位置**：[app/controllers/auth.py](file:///c:/Users/HuTao/Desktop/school/20260516/WorkSpace/Day4/cnAgentOS/app/controllers/auth.py)
- **职责**：
  - `LoginHandler`：处理 `/auth/login` 的 GET（渲染页面）和 POST（验证登录）
  - `LogoutHandler`：处理 `/auth/logout` 的 POST（清除 Cookie）

#### IndexHandler - 首页控制器
- **位置**：[app/controllers/home.py](file:///c:/Users/HuTao/Desktop/school/20260516/WorkSpace/Day4/cnAgentOS/app/controllers/home.py)
- **职责**：处理 `/` 路径的 GET 请求，展示后台页面

### Model 层（模型）

#### db.py - 数据库模块
- **位置**：[app/models/db.py](file:///c:/Users/HuTao/Desktop/school/20260516/WorkSpace/Day4/cnAgentOS/app/models/db.py)
- **核心函数**：
  - `get_connection()`：获取 SQLite 数据库连接，使用 `sqlite3.Row` 作为 row_factory（返回字典式行对象）
  - `init_db()`：初始化数据库表结构（创建 users 表）
  - `DB_PATH`：数据库文件路径常量

#### user.py - 用户模型
- **位置**：[app/models/user.py](file:///c:/Users/HuTao/Desktop/school/20260516/WorkSpace/Day4/cnAgentOS/app/models/user.py)
- **核心类**：`UserRepository`（用户仓储）
- **核心方法**：
  - `create_user(username, password)`：创建用户，返回 bool
  - `get_user_by_username(username)`：根据用户名查询用户
  - `verify_user(username, password)`：验证用户密码
- **加密方法**：`_hash_password(password, salt)` - PBKDF2-HMAC-SHA256

### View 层（视图）

#### 模板文件
- **base.html**：基础布局模板，使用 `{% block body %}{% end %}` 提供内容插槽
- **login.html**：登录表单页面，继承 base.html
- **index.html**：后台页面，显示用户名和退出按钮
- **register.html**：注册页面（已预留，内容为空，待实现）

#### 静态资源
- **base.css**：全局基础样式
- **base.js**：全局基础脚本

---

## 路由配置

| URL 路径 | 处理器 | 请求方法 | 功能说明 | 权限要求 |
|----------|--------|----------|----------|----------|
| `/` | IndexHandler | GET | 后台首页 | 需要登录 |
| `/auth/login` | LoginHandler | GET | 渲染登录页 | 公开 |
| `/auth/login` | LoginHandler | POST | 提交登录验证 | 公开 |
| `/auth/logout` | LogoutHandler | POST | 退出登录 | 需要登录 |
| `/login.jsp` | (框架内置) | GET | 未登录自动跳转页 | - |

---

## 数据库设计

### users 表

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,     -- 主键，自增
    username TEXT NOT NULL UNIQUE,            -- 用户名，唯一约束
    password_hash TEXT NOT NULL,              -- PBKDF2 哈希后的密码（十六进制字符串）
    salt TEXT NOT NULL,                       -- 随机盐值（十六进制字符串，16字节）
    created_at DATETIME DEFAULT(datetime('now','localtime'))  -- 创建时间，自动填充
)
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER | 用户唯一标识，自增主键 |
| `username` | TEXT | 用户名，不可重复 |
| `password_hash` | TEXT | 密码哈希值，格式为 hex 字符串 |
| `salt` | TEXT | 盐值，16 字节随机数，hex 编码 |
| `created_at` | DATETIME | 记录创建时间，使用本地时间 |

---

## 运行与配置

### 环境要求

- Python 3.12+
- Tornado 6.5.5

### 启动方式

```bash
# 启动服务（端口：10086）
python app.py
```

启动后访问：`http://localhost:10086`

### 默认测试账号

| 用户名 | 密码 |
|--------|------|
| admin | 123456 |

> 注：测试账号通过 `test.py` 脚本预先注册到数据库。

---

## 待实现功能

以下功能模块预留或尚未实现，可根据后续需求进行开发：

| 功能 | 状态 | 说明 |
|------|------|------|
| **用户注册页面** | 待实现 | View 层模板已预留，Controller 层待开发 |
| **密码找回/重置** | 待实现 | 无相关实现 |
| **会话管理** | 待实现 | 仅使用 Secure Cookie，无 Session 管理 |
| **API 接口** | 待实现 | 当前为传统 MPA 模式，无 RESTful API |
| **角色权限系统** | 待实现 | 无角色区分 |
| **数据看板** | 待实现 | 核心功能待开发 |
| **AI 智能问数** | 待实现 | 核心功能待开发 |
| **智能瞭望功能** | 待实现 | 核心功能待开发 |

---

## 开发规范

### 代码规范

1. **MVC 分层**：严格遵循 MVC 架构，Controller 负责处理请求和路由，Model 负责数据操作，View 负责页面渲染
2. **命名规范**：
   - Controller：`XxxHandler`（如 `LoginHandler`）
   - Model：`XxxRepository`（如 `UserRepository`）
   - 私有函数：`_xxx()` 下划线前缀
3. **类型注解**：使用 Python 3.12 类型提示（如 `def func(x: str) -> bool:`）

### 安全规范

1. **密码存储**：必须使用 PBKDF2 哈希，禁止明文存储
2. **XSRF 保护**：所有 POST 表单必须包含 `{% module xsrf_form_html() %}`
3. **Cookie 加密**：使用 `cookie_secret` 加密存储

### 数据库规范

1. 使用参数化查询（`?` 占位符），防止 SQL 注入
2. 使用 `sqlite3.Row` 作为 row_factory，通过列名访问数据
3. 使用 `with` 语句管理数据库连接

---

## 关键设计模式

### 仓储模式（Repository Pattern）

用户数据访问通过 `UserRepository` 类封装，提供静态方法：

```python
UserRepository.create_user(username, password)  → bool
UserRepository.get_user_by_username(username)   → sqlite3.Row | None
UserRepository.verify_user(username, password)  → bool
```

### 装饰器模式（Decorator Pattern）

使用 `@tornado.web.authenticated` 装饰器实现路由级别的权限控制：

```python
class IndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("index.html", ...)
```

### 模板继承模式

前端模板通过 `{% extends %}` 和 `{% block %}` 实现布局复用：

```
base.html (布局框架)
  ├── login.html (内容块：登录表单)
  ├── index.html (内容块：后台页面)
  └── register.html (内容块：注册表单，待实现)
```

---

## 注意事项

1. **数据库文件**：`database/app.db` 由 `init_db()` 自动创建和初始化，无需手动建表
2. **端口占用**：服务运行在 `10086` 端口，确保无冲突
3. **调试模式**：`debug=True` 在生产环境应关闭
4. **cookie_secret**：当前硬编码 `"123456"`，生产环境应使用环境变量或配置文件
5. **autoreload**：开发模式开启自动重载，生产环境建议关闭

---

## 文件清单

| 文件路径 | 类型 | 职责 |
|----------|------|------|
| `app.py` | 入口 | Tornado 应用配置、路由注册、服务启动 |
| `app/__init__.py` | 包标识 | 标记 app 为 Python 包 |
| `app/controllers/base.py` | Controller | 基础 Handler，登录态处理 |
| `app/controllers/auth.py` | Controller | 登录/登出业务逻辑 |
| `app/controllers/home.py` | Controller | 首页控制器 |
| `app/models/db.py` | Model | 数据库连接与初始化 |
| `app/models/user.py` | Model | 用户仓储与密码加密 |
| `app/templates/base.html` | View | 基础模板 |
| `app/templates/login.html` | View | 登录页面 |
| `app/templates/index.html` | View | 后台页面 |
| `app/templates/register.html` | View | 注册页面（空） |
| `app/static/css/base.css` | 静态 | 基础样式 |
| `app/static/js/base.js` | 静态 | 基础脚本 |
| `test.py` | 测试 | 用户模块测试脚本 |
| `database/app.db` | 数据 | SQLite 数据库文件 |
