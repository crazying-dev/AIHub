# AIHub

把多家大模型收敛到同一套 **OpenAI 兼容协议** 下的接入网关（Flask 应用名 ComputeRelay）：
一个密钥，改一行 `base_url` 就能切换模型。

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `main.py` | 后端入口：启动 Flask（127.0.0.1:2685）与后台常驻线程 |
| `route/` | 后端路由：`/api/sign*`（注册登录）、`/api/key*`（密钥）、`/v1/chat/completions`（兼容接口） |
| `database/` | PostgreSQL 数据层（SQLAlchemy），建表逻辑在 `InitDatabase.py` |
| `src/` | **前端**：Vue 3 + TypeScript + Vite + vue-router |
| `public/` | 静态资源（favicon） |

## 前端

### 页面路由

| 路由 | 页面 | 说明 |
| --- | --- | --- |
| `/` | 首页 | 产品介绍、支持的模型、调用示例 |
| `/register` | 注册 | 两步式：邮箱验证码 → 用户名 / 密码 |
| `/login` | 登录 | 对应后端 `POST /api/sign` |
| `/console` | 控制台 | 密钥列表 / 新建密钥 / 用量趋势 / 最近调用（需登录） |
| `/docs` | 接入文档 | 快速开始、鉴权、接口字段、错误码、SDK 示例 |
| `*` | 404 | 兜底页面 |

### 本地开发

```bash
pnpm install
pnpm dev      # http://localhost:5173
pnpm build    # vue-tsc 类型检查 + 生产构建到 dist/
```

`vite.config.ts` 里已经把 `/api`、`/v1` 代理到 `http://127.0.0.1:2685`，
所以本地只需另外启动后端（`uv run main.py`）即可联调，不存在跨域问题。

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
