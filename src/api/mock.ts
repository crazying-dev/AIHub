/** 后端不可用时使用的本地演示数据（仅用于 UI 预览） */

export interface ApiKeyItem {
  key: string
  label: string
  createdAt: string
  lastUsed: string
  status: 'active' | 'paused'
}

export interface UsageRow {
  id: string
  model: string
  tokens: number
  latency: number
  status: 'ok' | 'error'
  ts: string
}

export interface StatItem {
  label: string
  value: string
  delta: string
  tone: 'accent' | 'ok' | 'info'
}

export const demoKeys: ApiKeyItem[] = [
  {
    key: 'ah-3f9c1d47-2b6e-4a18-9c02-77ad5e0b1f34',
    label: '默认密钥',
    createdAt: '2026-08-02',
    lastUsed: '3 分钟前',
    status: 'active',
  },
  {
    key: 'ah-b7e04a12-9d35-4f8b-b1c6-5c2d90e7a483',
    label: '测试环境',
    createdAt: '2026-09-11',
    lastUsed: '2 天前',
    status: 'paused',
  },
]

export const demoStats: StatItem[] = [
  { label: '本月调用次数', value: '128,430', delta: '+12.4%', tone: 'accent' },
  { label: 'Token 消耗', value: '46.2 M', delta: '+8.1%', tone: 'info' },
  { label: '平均首字延迟', value: '428 ms', delta: '-6.3%', tone: 'ok' },
  { label: '可用模型', value: '12', delta: '4 个新上线', tone: 'accent' },
]

export const demoLogs: UsageRow[] = [
  { id: 'req_8f2c1', model: 'gpt-4o-mini', tokens: 1824, latency: 612, status: 'ok', ts: '10:24:51' },
  { id: 'req_8f2b7', model: 'claude-3-5-sonnet', tokens: 5240, latency: 1180, status: 'ok', ts: '10:23:08' },
  { id: 'req_8f2a3', model: 'deepseek-chat', tokens: 964, latency: 288, status: 'ok', ts: '10:21:44' },
  { id: 'req_8f299', model: 'qwen-max', tokens: 0, latency: 0, status: 'error', ts: '10:20:12' },
  { id: 'req_8f281', model: 'gpt-4o-mini', tokens: 2310, latency: 540, status: 'ok', ts: '10:18:37' },
]

export const demoModels: string[] = [
  'gpt-4o',
  'gpt-4o-mini',
  'claude-3-5-sonnet',
  'deepseek-chat',
  'qwen-max',
  'glm-4-plus',
]
