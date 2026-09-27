import type { CommunityKeyItem } from './types'

/**
 * 后端接口客户端。
 *
 * 约定（对应 route/api/*.py）：
 * - 鉴权靠浏览器 Cookie（httponly：token / id），所以所有请求都带 credentials: 'include'；
 * - 成功一般返回 "OK" / "Cookie" 文本，失败返回 401 或 {"error": "..."}；
 * - 开发环境下由 vite.config.ts 的 proxy 把 /api、/v1 转发到 Flask(127.0.0.1:2685)。
 *
 * 后端不可用时一律抛错交给页面提示，不做本地假数据降级。
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

/** 请求未能到达后端（服务未启动 / 断网 / CORS 拦截） */
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

/** 上传社区 key 的表单载荷 */
export interface CommunityKeyPayload {
  url: string
  key: string
  model: string
  protocol: string
  name?: string
  priority?: number
  maxuse?: number | null
  text?: string
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

  /**
   * 注册第一步：POST /api/sign/up/1，由后端通过 163 SMTP 发验证码。
   * 后端会给出具体原因（邮箱格式 / 60 秒冷却 / 邮件服务未配置），这里原样透出。
   */
  async sendSignUpCode(email: string): Promise<void> {
    const res = await request('/api/sign/up/1', { body: { email } })
    if (!res.ok) throw await failure(res, '验证码发送失败，请稍后重试')
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
    if (!res.ok) throw await failure(res, res.status === 401 ? '状态已失效，请重新登录' : '创建密钥失败')
  },

  /** 吊销（删除）自己的个人密钥：POST /api/key/delete，key 带不带 ah- 前缀都行 */
  async deleteKey(key: string): Promise<void> {
    const res = await request('/api/key/delete', { body: { key } })
    if (!res.ok) throw await failure(res, '吊销失败')
  },

  /** 社区池全部条目：POST /api/community/pool（公开可浏览，自己的条目标记 mine） */
  async listCommunityPool(): Promise<CommunityKeyItem[]> {
    const res = await request('/api/community/pool')
    if (!res.ok) throw await failure(res, '社区池加载失败')
    const data: unknown = await res.json()
    if (!Array.isArray(data)) return []
    return (data as RawCommunityKey[]).map(toCommunityItem)
  },

  /** 社区池：上传自己的上游 key，返回可直接使用的社区密钥 ah-xxxx：POST /api/community/upload */
  async uploadCommunityKey(payload: CommunityKeyPayload): Promise<string> {
    const res = await request('/api/community/upload', { body: payload })
    if (!res.ok) throw await failure(res, '上传失败')
    const data = (await res.json()) as { key?: string }
    return String(data.key ?? '')
  },

  /** 社区池：删除自己上传的 key：POST /api/community/delete */
  async deleteCommunityKey(id: string): Promise<void> {
    const res = await request('/api/community/delete', { body: { id } })
    if (!res.ok) throw await failure(res, '删除失败')
  },
}

/** 后端 otherkey 行的原始字段（下划线命名，mine 由 pool 接口按登录态给出） */
interface RawCommunityKey {
  id: string
  key: string
  url: string
  model: string
  name: string | null
  protocol: string
  priority: number
  maxuse: number | null
  used: number
  remaining: number | null
  enabled: boolean
  text: string | null
  created_at: number
  mine?: boolean
}

function toCommunityItem(raw: RawCommunityKey): CommunityKeyItem {
  return {
    id: String(raw.id),
    key: String(raw.key ?? ''),
    url: String(raw.url ?? ''),
    model: String(raw.model ?? ''),
    name: raw.name ?? null,
    protocol: String(raw.protocol ?? ''),
    priority: Number(raw.priority ?? 0),
    maxuse: raw.maxuse === null || raw.maxuse === undefined ? null : Number(raw.maxuse),
    used: Number(raw.used ?? 0),
    remaining: raw.remaining === null || raw.remaining === undefined ? null : Number(raw.remaining),
    enabled: Boolean(raw.enabled),
    text: raw.text ?? null,
    createdAt: Number(raw.created_at ?? 0),
    mine: Boolean(raw.mine),
  }
}

/** 把后端的错误响应（{error: ...} 或 {error: {message}}）转成可提示的 HttpError */
async function failure(res: Response, fallback: string): Promise<HttpError> {
  let message = fallback
  try {
    const data: unknown = await res.json()
    if (data && typeof data === 'object') {
      const error = (data as { error?: unknown }).error
      if (typeof error === 'string') {
        message = error
      } else if (error && typeof error === 'object') {
        const inner = (error as { message?: unknown }).message
        if (typeof inner === 'string') message = inner
      }
    }
  } catch {
    /* 后端没回 JSON，用兜底文案 */
  }
  return new HttpError(res.status, message)
}