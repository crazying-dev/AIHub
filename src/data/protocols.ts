/** 接入文档页「多协议接入」区块的数据（与后端 route/proxy/ 的入站端点保持一致） */
import { API_HOST } from './snippets'

export interface RelayEndpoint {
  method: 'GET' | 'POST'
  path: string
  desc: string
}

export interface ProtocolCard {
  id: string
  label: string
  path: string
  desc: string
  auth: string
  code: string
}

export const relayEndpoints: RelayEndpoint[] = [
  { method: 'POST', path: '/v1/chat/completions', desc: 'OpenAI Chat Completions（最常用的入口）' },
  { method: 'POST', path: '/v1/completions', desc: 'OpenAI Completions（legacy 文本补全）' },
  { method: 'POST', path: '/v1/responses', desc: 'OpenAI Responses API（input / instructions / 函数调用）' },
  { method: 'POST', path: '/v1/embeddings', desc: 'OpenAI Embeddings（只有 openai 协议的上游 key 支持）' },
  { method: 'GET', path: '/v1/models', desc: '当前调用方可用的模型标识（含 auto）' },
  { method: 'POST', path: '/v1/messages', desc: 'Anthropic Messages' },
  { method: 'POST', path: '/v1/messages/count_tokens', desc: 'Anthropic 令牌计数（本地估算）' },
  { method: 'POST', path: '/api/chat', desc: 'Ollama 对话（NDJSON 流）' },
  { method: 'POST', path: '/api/generate', desc: 'Ollama 补全（NDJSON 流）' },
  { method: 'GET', path: '/api/tags', desc: 'Ollama 模型列表' },
  { method: 'GET', path: '/api/version · /api/ps', desc: 'Ollama 版本 / 常驻模型' },
  { method: 'POST', path: '/api/show', desc: 'Ollama 模型详情' },
  { method: 'POST', path: '/v1beta/models/{model}:generateContent', desc: 'Gemini 原生对话' },
  { method: 'POST', path: '/v1beta/models/{model}:streamGenerateContent', desc: 'Gemini 原生对话（SSE 流）' },
  { method: 'POST', path: '/v1beta/models/{model}:countTokens', desc: 'Gemini 令牌计数（本地估算）' },
  { method: 'GET', path: '/v1beta/models', desc: 'Gemini 模型列表' },
]

export const protocols: ProtocolCard[] = [
  {
    id: 'openai',
    label: 'OpenAI',
    path: '/v1/chat/completions',
    desc: '任何支持自定义 base_url 的 OpenAI 兼容客户端，把地址换成网关地址即可。',
    auth: 'Authorization: Bearer ah-xxxx',
    code: `curl ${API_HOST}/v1/chat/completions \\
  -H "Authorization: Bearer ah-xxxx" \\
  -H "Content-Type: application/json" \\
  -d '{"model": "auto", "messages": [{"role": "user", "content": "hi"}]}'`,
  },
  {
    id: 'responses',
    label: 'OpenAI Responses',
    path: '/v1/responses',
    desc: '新版 OpenAI SDK / Codex CLI 使用的 Responses API，支持 input items、instructions 与函数调用。',
    auth: 'Authorization: Bearer ah-xxxx',
    code: `curl ${API_HOST}/v1/responses \\
  -H "Authorization: Bearer ah-xxxx" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "auto",
    "instructions": "你是简洁的助手",
    "input": "用一句话介绍模型网关"
  }'`,
  },
  {
    id: 'anthropic',
    label: 'Anthropic',
    path: '/v1/messages',
    desc: 'Claude Code / Anthropic SDK 直接可用，另有 /v1/messages/count_tokens 供上下文预算使用。',
    auth: 'x-api-key: ah-xxxx',
    code: `curl ${API_HOST}/v1/messages \\
  -H "x-api-key: ah-xxxx" \\
  -H "anthropic-version: 2023-06-01" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "auto",
    "max_tokens": 256,
    "messages": [{"role": "user", "content": "hi"}]
  }'`,
  },
  {
    id: 'ollama',
    label: 'Ollama',
    path: '/api/chat',
    desc: '把 OLLAMA_HOST 指向网关即可，NDJSON 流式；不带凭证时自动使用公共库 ah-xxxx。',
    auth: 'Authorization: Bearer ah-xxxx（可省略）',
    code: `# 让 Ollama 系列客户端指向网关
export OLLAMA_HOST=${API_HOST}

curl ${API_HOST}/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{"model": "auto", "messages": [{"role": "user", "content": "hi"}], "stream": false}'`,
  },
  {
    id: 'gemini',
    label: 'Gemini',
    path: '/v1beta/models/{model}:generateContent',
    desc: 'Google 原生 REST 风格，替换 generativelanguage 的 baseUrl 即可；支持 SSE 流式与 countTokens。',
    auth: '?key=ah-xxxx 或 x-goog-api-key',
    code: `curl "${API_HOST}/v1beta/models/auto:generateContent?key=ah-xxxx" \\
  -H "Content-Type: application/json" \\
  -d '{"contents": [{"role": "user", "parts": [{"text": "hi"}]}]}'`,
  },
]