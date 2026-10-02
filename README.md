# AIHub

把多家大模型收敛到同一套 **OpenAI 兼容协议** 下的接入网关（Flask 应用名 ComputeRelay）：
一个密钥，改一行 `base_url` 就能切换模型。

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `main.py` | 后端入口：启动 Flask（127.0.0.1:2685）与后台常驻线程 |
| `route/` | 后端路由：`/api/sign*`（注册登录）、`/api/key*`（个人密钥）、`/api/private/*`（私有库）、`/api/community/*`（公共库）；`route/proxy/` 是模型中继的入站协议路由 |
| `database/` | PostgreSQL 数据层（SQLAlchemy），建表逻辑在 `InitDatabase.py` |
| `database/community/` | 公共库（`otherkey` 表）的增删查、候选调度与用量累计 |
| `database/private/` | 私有库（`privatekey` 表）的增删查、按授权范围过滤候选与用量累计 |
| `protocol/` | 多协议适配层：入站 OpenAI / Responses / Ollama / Anthropic / Gemini，上游 OpenAI / Anthropic / Gemini，负责请求、响应与流式事件的双向转换 |
| `Relay.py` | 中继核心：按 `model` 选候选 key → 协议转换 → 调用上游 |
| `Mail.py` | 注册验证码邮件发送（163 邮箱 SMTP，配置见 `.env.example`） |
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
SMTP_USER=ourpet001@163.com
SMTP_PASSWORD=<163 授权码>
```

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | 是 | PostgreSQL 连接串（不写驱动时按 psycopg2 处理）；缺失时启动会直接抛出明确错误 |
| `SMTP_PASSWORD` | 是 | 163 邮箱**授权码**（在邮箱设置的 POP3/SMTP/IMAP 里开启服务时生成，不是网页登录密码）；不配置时注册接口返回 500「邮件服务未配置」 |
| `SMTP_USER` | 否 | 发件邮箱，默认 `ourpet001@163.com`（发信地址要与它一致，否则会被 535 / 553 拒绝） |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_TLS` | 否 | 发信服务器，默认 `smtp.163.com` / `465` / `ssl`（可选 `starttls` 587、`none` 明文） |
| `SMTP_TIMEOUT` | 否 | 发信超时秒数，默认 20 |
| `SMTP_FROM_NAME` | 否 | 发件人显示名，默认 `AIHub` |

> 注册验证码是随机 6 位，由 `Mail.py` 经 163 SMTP 发送（主题「AIHub 注册验证码」），
> **5 分钟内有效**：`database/persistent.py` 每秒清理 `email` 表里超过 300 秒的记录。
> 同一邮箱 60 秒内只能发一次（重复请求返回 429）；发信是同步的（163 约 1~3 秒），
> 失败时返回 502，具体原因（授权码错误 / 超时）只打在后端控制台，不暴露给前端。

前端构建产物 `dist/` 已随仓库提交，部署机上不需要 Node / pnpm；若 `dist/` 缺失，`/` 会返回 503 并提示先构建。

## 后端接口

### 模型中继（五种客户端协议入站）

所有入口共用同一套鉴权与路由规则（见下节），最终都按所选上游 key 的协议发起调用。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/v1/chat/completions` | OpenAI Chat Completions 入站，字段与官方一致，支持 `stream` |
| `POST` | `/v1/completions` | OpenAI Completions（legacy）入站，返回 `text_completion` 结构 |
| `POST` | `/v1/responses` | OpenAI Responses API 入站（`input` / `instructions` / 函数调用，带事件名的 SSE 流） |
| `POST` | `/v1/embeddings` | OpenAI Embeddings 入站（只有 `openai` 协议的上游 key 支持） |
| `GET` | `/v1/models` | 当前调用方（公共库 / 私有库）可用的模型标识（含 `auto`） |
| `POST` | `/v1/messages` | Anthropic Messages 入站，支持流式 SSE |
| `POST` | `/v1/messages/count_tokens` | Anthropic 令牌计数（本地估算） |
| `POST` | `/api/chat` | Ollama 对话入站（NDJSON 流） |
| `POST` | `/api/generate` | Ollama 补全入站（NDJSON 流） |
| `GET` | `/api/tags` | Ollama 模型列表 |
| `GET` | `/api/version`・`/api/ps` | Ollama 版本号 / 常驻模型（中继无常驻模型，返回空列表） |
| `POST` | `/api/show` | Ollama 模型详情 |
| `POST` | `/v1beta/models/{model}:generateContent` | Gemini 原生对话 |
| `POST` | `/v1beta/models/{model}:streamGenerateContent` | Gemini 原生对话（SSE 流） |
| `POST` | `/v1beta/models/{model}:countTokens` | Gemini 令牌计数（本地估算） |
| `GET` | `/v1beta/models` | Gemini 模型列表 |


鉴权（所有入站入口通用）：`Authorization: Bearer <key>`；Anthropic 入口也接受 `x-api-key`，Gemini 入口接受 `?key=`，Ollama 入口不带凭证时退回公共库 `ah-xxxx`。两种 key：

- **`ah-xxxx`（固定字面量，就是四个 x，不可更换）**：公共库凭证，**任何人**带上它就能调用
  公共库（社区池）里的全部 key，不需要注册、也不需要新建密钥；
- **`ah-<id>`（个人密钥）**：只调度**自己**私有库里的上游 key，并且要落在该密钥的 `canuse`
  授权范围内（为空 = 可以使用全部私有 key）。

网关会把本次命中的 key 与模型回传到响应头 `X-AIHub-Key` / `X-AIHub-Model`，便于排查路由结果。

### 客户端兼容层

中继面（`/v1/*`、`/v1beta/*`、Ollama 的 `/api/<动作>`）统一做了一组容错，实现见 `route/proxy/Compat.py`：

- **跨域（CORS）**：浏览器里的 Web 客户端可以直接直连。`OPTIONS` 预检返回 `Access-Control-Allow-Origin: *`
  （鉴权走请求头、不用 Cookie，所以不带凭据），允许的请求头按预检里的声明回显，并用
  `Access-Control-Expose-Headers` 把 `X-AIHub-Key` / `X-AIHub-Model` 暴露给页面。
  管理面 `/api/*`（sign / key / community / private，走 Cookie 鉴权）**不参与跨域**；
- **结尾斜杠容错**：`POST /v1/chat/completions/` 这类多一个斜杠的地址照常处理，不再因为
  Flask 的 `strict_slashes` 返回 `405`（客户端 `base_url` 末尾带 `/` 时很常见）；
- **错误 JSON 化**：中继面上出现 `404` / `405` 时，按对应协议返回 JSON 错误体
  （OpenAI / Anthropic / Gemini / Ollama 各自的形状）并带上 `Allow` 头，
  不再回一坨客户端解析不了的 HTML。

### 两套 key 库与 model 路由

上游厂商的 key（OpenAI / Anthropic / Gemini）分两处存放（实现见 `Relay.py`）：

- **公共库**（`otherkey` 表，导航栏「社区」页）——对所有人开放，调用凭证是固定字面量
  `ah-xxxx`，无需注册即可使用，库内全部 key 都能被路由到；
- **私有库**（`privatekey` 表，导航栏「私有库」页）——只给本人的个人密钥 `ah-<id>` 使用。
  每条个人密钥带一个 `canuse` 授权范围：为空表示可以使用全部私有 key，非空则只在这些 key
  里路由（公共库、别人的私有 key 都碰不到）；私有库的 id 不是凭证，`ah-<privatekey id>` 无效。

`model` 的取值决定在**所选库内**怎么挑 key：

| `model` 取值 | 行为 |
| --- | --- |
| `auto`（或留空） | 在所选库内按优先级自动挑 |
| 具体模型名 | 先按上传时填写的 `model` 名匹配；全都匹配不上，再按上传者给 key 起的 `name` 兜底 |
| 全部不匹配 | 找不到任何候选 ⇒ `503 no_available_key` |

排序与限额：

- `priority` 数值越大越优先（默认 50），同优先级下按已用次数升序、上传时间升序；
- 上传时可设置 `maxuse`；**每次真正打到上游就 +1（失败也计）**，用满后该 key 自动跳过，尝试下一个候选；
- 候选全部调用失败 ⇒ `502 upstream_error`。

### 协议转换

上游支持 `openai` / `anthropic` / `gemini` 三种协议（走各自官方 SDK）；入站支持 OpenAI Chat Completions、
OpenAI Responses、OpenAI Completions(legacy)、OpenAI Embeddings、Anthropic Messages、Ollama、Gemini 原生。
`protocol/` 把入站请求归一化为内部规范格式，再把上游响应 / 流式事件转换回调用方协议，
因此用 OpenAI 客户端调一把 Anthropic 上游 key、或用 Ollama 客户端调 Gemini key 都是可行的。

> 当前限制：Gemini 上游仅支持文本 / 图片，工具调用不做转换；
> `count_tokens` 是本地估算（上游协议各异，没有统一分词器），只适合做上下文预算；
> `embeddings` 只支持 `openai` 协议的上游 key；
> 流式调用只在「建立上游请求」阶段失败时才会切换下一个候选，流开始后的上游报错会原样透传给调用方。

### 管理接口（Cookie 鉴权）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/key/new` | 新建个人密钥，可带 `{"canuse": ["<privatekey id>", ...]}` 指定授权范围（缺省 = 全部私有 key） |
| `POST` | `/api/key/list` | 当前用户的个人密钥列表（含授权范围 `canuse` / `all`） |
| `POST` | `/api/key/scope` | 修改某条个人密钥的授权范围，body 传 `{"key": "ah-xxxx", "canuse": [...]}` |
| `POST` | `/api/key/get` | 个人密钥列表（只返回 `ah-xxxx` 字符串，兼容旧接口） |
| `POST` | `/api/key/delete` | 吊销（删除）自己的个人密钥，body 传 `{"key": "ah-xxxx"}` |
| `POST` | `/api/private/upload` | 上传自己的上游 key 到私有库（只给自己用），返回 `{"id": "<privatekey id>"}` |
| `POST` | `/api/private/list` | 我的私有库全部条目（上游密钥已打码，不返回 `userid`） |
| `POST` | `/api/private/delete` | 删除自己私有库里的某条 key，body 传 `{"id": "..."}` |
| `POST` | `/api/community/pool` | 公共库全部条目（**公开**，无需登录；上游密钥已打码，不返回 `userid`，自己上传的条目标记 `mine=true`） |
| `POST` | `/api/community/upload` | 上传自己的上游 key 到公共库 |
| `POST` | `/api/community/list` | 当前用户上传的公共库 key（上游密钥已打码，并给出剩余次数） |
| `POST` | `/api/community/delete` | 删除自己上传的公共库 key |

上传字段：`url`、`key`、`model` 必填；`protocol`（`openai` / `anthropic` / `gemini`，缺省 openai）、
`name`、`priority`（默认 50）、`maxuse`、`text`（备注）可选。

## 前端

### 页面路由

| 路由 | 页面 | 说明 |
| --- | --- | --- |
| `/` | 首页 | 产品介绍、支持的模型、调用示例 |
| `/register` | 注册 | 两步式：邮箱验证码 → 用户名 / 密码 |
| `/login` | 登录 | 对应后端 `POST /api/sign` |
| `/console` | 控制台 | 密钥列表 / 新建密钥 / 设置授权范围 / 吊销密钥（需登录） |
| `/community` | 社区 | 公共库：固定凭证 `ah-xxxx`、浏览、上传自己的上游 key、删除自己上传的条目 |
| `/library` | 私有库 | 只给自己用的上游 key：上传 / 删除（需登录） |
| `/docs` | 接入文档 | 快速开始、鉴权、接口字段、多协议接入、公共库 / 私有库与模型路由、错误码、SDK 示例 |
| `*` | 404 | 兜底页面 |

### 本地开发

```bash
pnpm install
pnpm dev      # http://localhost:5173
pnpm build    # vue-tsc 类型检查 + 生产构建到 dist/
```

`vite.config.ts` 里已经把 `/api`、`/v1`（前缀匹配，含 `/v1beta`）代理到 `http://127.0.0.1:2685`，
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
| `/api/*`、`/v1/*`、`/v1beta/*` | 只走后端接口，不会被前端吞掉（找不到就 404） |
| `dist/` 不存在 | 返回 503 与“请先执行 pnpm build”的提示 |

产物目录默认是 `<项目根>/dist`，可用环境变量 `AIHUB_DIST` 指向别处。


### 数据来源

界面上的数据全部来自后端真实接口，**没有本地假数据降级**：

- 后端连不上（服务未启动 / 断网 / CORS 拦截）时，`src/api/client.ts` 抛 `NetworkError`，
  由页面直接提示错误，不再回退到占位数据；
- 业务错误（401 / 500 等）不会降级，仍按真实错误提示；
- 登录态保存在 HttpOnly Cookie 中（前端不可读），前端仅在 `localStorage` 存一份用于展示的用户资料；
  控制台发起真实请求拿到 401 时会自动登出并跳回登录页；
- 用量统计、调用日志等后端尚未实现的看板已从控制台移除，避免展示编造的数字。

### 其他

- 样式体系见 `src/style.css`（设计令牌 + 亮/暗主题，跟随系统或手动切换）；
- 图标为 `src/components/AppIcon.vue` 内置的描边图标集，未引入任何 UI/图标库。
