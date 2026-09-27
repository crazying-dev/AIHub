# AIHub

把多家大模型收敛到同一套 **OpenAI 兼容协议** 下的接入网关（Flask 应用名 ComputeRelay）：
一个密钥，改一行 `base_url` 就能切换模型。

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `main.py` | 后端入口：启动 Flask（127.0.0.1:2685）与后台常驻线程 |
| `route/` | 后端路由：`/api/sign*`（注册登录）、`/api/key*`（密钥）、`/api/community/*`（社区 key）、`/v1/*`（模型中继） |
| `database/` | PostgreSQL 数据层（SQLAlchemy），建表逻辑在 `InitDatabase.py` |
| `database/community/` | 社区 key 池（`otherkey` 表）的增删查、候选调度与用量累计 |
| `protocol/` | 多协议适配层：OpenAI / Anthropic / Gemini 的请求、响应与流式事件双向转换 |
| `Relay.py` | 中继核心：按 `model` 选候选 key → 协议转换 → 调用上游 |
| `src/` | **前端**：Vue 3 + TypeScript + Vite + vue-router |
| `public/` | 静态资源（favicon） |

## 运行与环境变量

依赖与版本已锁定在 `pyproject.toml` / `uv.lock` 中，直接用 uv 启动即可：

```bash
uv run main.py        # 自动安装依赖并启动 Flask（127.0.0.1:2685）
```

（也可以 `uv pip install -r requirements.txt` 后用 `python main.py` 运行。）

依赖：`flask`（Web）、`psycopg2-binary` + `sqlalchemy`（PostgreSQL）、`python-dotenv`（读取 `.env`），
以及协议适配层使用的官方 SDK：`openai`、`anthropic`、`google-genai`。
SQLAlchemy 2.1 带来两个坑，仓库里已处理：

- `postgresql://` 的默认驱动变成了 psycopg(3)，本项目用的是 psycopg2，`database/conn.py` 里把驱动显式指定了；
- `Row` 的下标只支持整数（内部就是元组），`row["字段名"]` 会抛 `TypeError: tuple indices must be integers or slices, not str`，
  取字段请统一用 `result.mappings()`（例：`database/user/get.py`）。

### .env

`.env` 不入库（见 `.gitignore`），部署时手动在项目根目录创建，字段可参考仓库里的 `.env.example`：

```bash
DATABASE_URL=postgresql://<用户>:<密码>@<主机>:5432/aihub?sslmode=disable
```

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | 是 | PostgreSQL 连接串（不写驱动时按 psycopg2 处理）；缺失时启动会直接抛出明确错误 |

> 注册验证码是随机 6 位，而注册邮件的发送逻辑还是占位（`route/api/sign.py` 里的
> `# 此处写邮箱发送逻辑`）：现在收不到邮件，需要从数据库 `email` 表里取 `code` 完成注册。

前端构建产物 `dist/` 已随仓库提交，部署机上不需要 Node / pnpm；若 `dist/` 缺失，`/` 会返回 503 并提示先构建。

## 后端接口

### 模型中继（OpenAI / Anthropic 双协议入站）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/v1/chat/completions` | OpenAI 兼容入站，字段与官方一致，支持 `stream` |
| `POST` | `/v1/messages` | Anthropic Messages 入站，支持流式 SSE |
| `GET` | `/v1/models` | 社区池当前可用的模型标识（含 `auto`） |

鉴权用 `Authorization: Bearer ah-`；调用 Anthropic 入站时也接受 `x-api-key: ah-xxxx`。
**任意一个有效的 `ah-` 密钥**（个人密钥或社区密钥）都能调用，网关会把本次命中的 key 与模型
回传到响应头 `X-AIHub-Key` / `X-AIHub-Model`，便于排查路由结果。

### 社区 key 池与 model 路由

「社区 key」指用户把自己的上游厂商 key（OpenAI / Anthropic / Gemini）上传到池子里供所有人共用，
上传后对外的密钥形态统一是 `ah-xxxx`。`model` 的取值决定怎么挑 key（实现见 `Relay.py`）：

| `model` 取值 | 行为 |
| --- | --- |
| `auto`（或留空） | 在整个池子里按优先级自动挑 |
| 具体模型名 | 先按上传时填写的 `model` 名匹配；全都匹配不上，再按上传者给 key 起的 `name` 兜底 |
| 全部不匹配 | 找不到任何候选 ⇒ `503 no_available_key` |

排序与限额：

- `priority` 数值越大越优先（默认 50），同优先级下按已用次数升序、上传时间升序；
- 上传时可设置 `maxuse`；**每次真正打到上游就 +1（失败也计）**，用满后该 key 自动跳过，尝试下一个候选；
- 候选全部调用失败 ⇒ `502 upstream_error`。

### 协议转换

上游支持 `openai` / `anthropic` / `gemini` 三种协议（走各自官方 SDK），入站支持 OpenAI 与 Anthropic。
`protocol/` 会把入站请求归一化为内部规范格式，再把上游响应 / 流式事件转换回调用方协议，
因此用 OpenAI 客户端调用一把 Anthropic 上游 key 也是可行的。

> 当前限制：Gemini 上游仅支持文本 / 图片，工具调用不做转换，且不能作为入站协议；
> 流式调用只在「建立上游请求」阶段失败时才会切换下一个候选，流开始后的上游报错会原样透传给调用方。

### 管理接口（Cookie 鉴权）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/community/upload` | 上传自己的上游 key 到社区池，返回 `ah-xxxx` |
| `POST` | `/api/community/list` | 当前用户上传的社区 key（上游密钥已打码，并给出剩余次数） |
| `POST` | `/api/community/delete` | 删除自己上传的社区 key |

上传字段：`url`、`key`、`model` 必填；`protocol`（`openai` / `anthropic` / `gemini`，缺省 openai）、
`name`、`priority`（默认 50）、`maxuse`、`text`（备注）可选。

## 前端

### 页面路由

| 路由 | 页面 | 说明 |
| --- | --- | --- |
| `/` | 首页 | 产品介绍、支持的模型、调用示例 |
| `/register` | 注册 | 两步式：邮箱验证码 → 用户名 / 密码 |
| `/login` | 登录 | 对应后端 `POST /api/sign` |
| `/console` | 控制台 | 密钥列表 / 新建密钥 / **社区 Key 面板**（上传 / 列表 / 删除 / 用量）/ 用量趋势 / 最近调用（需登录） |
| `/docs` | 接入文档 | 快速开始、鉴权、接口字段、社区池与模型路由、错误码、SDK 示例 |
| `*` | 404 | 兜底页面 |

### 本地开发

```bash
pnpm install
pnpm dev      # http://localhost:5173
pnpm build    # vue-tsc 类型检查 + 生产构建到 dist/
```

`vite.config.ts` 里已经把 `/api`、`/v1` 代理到 `http://127.0.0.1:2685`，
所以本地只需另外启动后端（`uv run main.py`）即可联调，不存在跨域问题。

> 提交约定：`dist/` 是入库的。改完 `src/` 后要执行 `pnpm build`，并把 `dist/` 一起提交，
> 否则部署机拉到的还是旧页面。`vite build` 会清空 `dist/` 再输出（文件名带内容哈希），
> 所以直接 `git add dist` 即可，不会残留旧产物。

### 部署：Flask 直接接管 dist

生产环境不需要 nginx：后端自身会把打包产物发出去（见 `route/web.py`）。

```bash
uv run main.py      # http://127.0.0.1:2685 直接就是前端页面（dist/ 已在仓库里）
```

`dist/` 已随仓库提交，因此服务器上不需要安装 Node / pnpm，拉下来即可运行；
只有改动前端时才需要本地 `pnpm build` 并把 `dist/` 一并提交。

路由规则：

| 请求 | 行为 |
| --- | --- |
| `/`、`/console`、`/docs` … | 返回 `dist/index.html`（history 模式路由刷新不 404） |
| `/assets/*` | 返回构建产物，`Cache-Control: public, max-age=31536000, immutable` |
| `/api/*`、`/v1/*` | 只走后端接口，不会被前端吞掉（找不到就 404） |
| `dist/` 不存在 | 返回 503 与“请先执行 pnpm build”的提示 |

产物目录默认是 `<项目根>/dist`，可用环境变量 `AIHUB_DIST` 指向别处。


### 演示模式（后端未就绪时）

后端核心业务仍在开发中，因此前端做了一层降级：

- 请求因为「连接不上后端」失败（服务未启动 / 断网）时，`src/api/client.ts` 会打开演示模式，
  页面改用 `src/api/mock.ts` 的本地数据渲染，并在顶部显示提示条；
- 业务错误（401 / 500 等）不会降级，仍按真实错误提示；
- 登录态保存在 HttpOnly Cookie 中（前端不可读），前端仅在 `localStorage` 存一份用于展示的用户资料；
  控制台发起真实请求拿到 401 时会自动登出并跳回登录页。

### 其他

- 样式体系见 `src/style.css`（设计令牌 + 亮/暗主题，跟随系统或手动切换）；
- 图标为 `src/components/AppIcon.vue` 内置的描边图标集，未引入任何 UI/图标库。
