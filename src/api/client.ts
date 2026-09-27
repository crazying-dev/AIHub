import { demo } from '../store/demo'

/**
 * 后端接口客户端。
 *
 * 约定（对应 route/api/*.py）：
 * - 鉴权靠浏览器 Cookie（httponly：token / id），所以所有请求都带 credentials: 'include'；
 * - 成功一般返回 "OK" / "Cookie" 文本，失败返回 401；
 * - 开发环境下由 vite.config.ts 的 proxy 把 /api、/v1 转发到 Flask(127.0.0.1:2685)。
 *
 * 说明：后端尚未完成的接口（如用量统计、日志）暂未对接，页面里用本地演示数据占位。
 */

const API_BASE: string = (import.meta.env.VITE_API_BASE as string | undefined) ?? ''

/** 后端返回非 2xx */
export class HttpError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'HttpError'
    this.status = status
  }
}

/** 请求未能到达后端（服务未启动 / 断网 / CORS 拦截），用于切换到演示数据 */
export class NetworkError extends Error {
  constructor(message = '无法连接到后端服务') {
    super(message)
    this.name = 'NetworkError'
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST'
  body?: unknown
}

async function request(path: string, options: RequestOptions = {}): Promise<Response> {
  const { method = 'POST', body } = options
  try {
    return await fetch(`${API_BASE}${path}`, {
      method,
      credentials: 'include',
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch (error) {
    throw new NetworkError(error instanceof Error ? error.message : undefined)
  }
}

interface SignUpPayload {
  email: string
  code: string
  name: string
  password: string
}

export const api = {
  /** 登录：POST /api/sign，成功后后端写入 Cookie */
  async signIn(email: string, password: string): Promise<void> {
    const res = await request('/api/sign', { body: { email, password } })
    if (!res.ok) {
      throw new HttpError(
        res.status,
        res.status === 401 ? '邮箱或密码不正确' : `登录失败（HTTP ${res.status}）`,
      )
    }
  },

  /** 注册第一步：POST /api/sign/up/1，向后端登记的邮箱发送验证码 */
  async sendSignUpCode(email: string): Promise<void> {
    const res = await request('/api/sign/up/1', { body: { email } })
    if (!res.ok) {
      throw new HttpError(res.status, '验证码发送失败，请稍后重试')
    }
  },

  /** 注册第二步：POST /api/sign/up/2，校验验证码并创建用户 */
  async signUp(payload: SignUpPayload): Promise<void> {
    const res = await request('/api/sign/up/2', { body: payload })
    if (!res.ok) {
      throw new HttpError(
        res.status,
        res.status === 401 ? '验证码不正确或已过期' : `注册失败（HTTP ${res.status}）`,
      )
    }
  },

  /** 查询当前用户的密钥列表：POST /api/key/get -> ["ah-xxx", ...] */
  async listKeys(): Promise<string[]> {
    const res = await request('/api/key/get')
    if (!res.ok) {
      throw new HttpError(
        res.status,
        res.status === 401 ? '登录状态已失效，请重新登录' : `获取密钥失败（HTTP ${res.status}）`,
      )
    }
    const data: unknown = await res.json()
    if (!Array.isArray(data)) return []
    return data.map((item) => String(item))
  },

  /** 新建密钥：POST /api/key/new */
  async createKey(): Promise<void> {
    const res = await request('/api/key/new')
    if (!res.ok) {
      throw new HttpError(
        res.status,
        res.status === 401 ? '登录状态已失效，请重新登录' : `创建密钥失败（HTTP ${res.status}）`,
      )
    }
  },
}

/**
 * 执行真实请求；若属于「后端没起来」的网络错误，则打开演示模式并回退到 fallback。
 * 业务错误（401/500 等）仍照常抛出，交给页面提示。
 */
export async function withDemo<T>(
  task: () => Promise<T>,
  fallback: () => T | Promise<T>,
): Promise<T> {
  try {
    return await task()
  } catch (error) {
    if (error instanceof NetworkError) {
      demo.activate()
      return await fallback()
    }
    throw error
  }
}
