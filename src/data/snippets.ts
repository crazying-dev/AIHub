/** 文档/首页展示用的调用示例（与后端 /v1/chat/completions 对接） */

export interface Snippet {
  label: string
  language: string
  code: string
}

export const API_HOST = 'http://127.0.0.1:2685'
export const CHAT_ENDPOINT = `${API_HOST}/v1/chat/completions`

export const chatSnippets: Snippet[] = [
  {
    label: 'cURL',
    language: 'bash',
    code: `curl ${CHAT_ENDPOINT} \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer $AIHUB_KEY" \\
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "用一句话解释什么是模型网关"}
    ]
  }'`,
  },
  {
    label: 'Python',
    language: 'python',
    code: `import os
from openai import OpenAI

client = OpenAI(
    base_url="${API_HOST}/v1",
    api_key=os.environ["AIHUB_KEY"],
)

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "你好，AIHub"}],
)
print(resp.choices[0].message.content)`,
  },
  {
    label: 'Node.js',
    language: 'javascript',
    code: `import OpenAI from 'openai'

const client = new OpenAI({
  baseURL: '${API_HOST}/v1',
  apiKey: process.env.AIHUB_KEY,
})

const resp = await client.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [{ role: 'user', content: '你好，AIHub' }],
})
console.log(resp.choices[0].message.content)`,
  },
]

export const curlQuickstart = `# 1. 登录后在控制台创建密钥，拿到 ah-xxxx
# 2. 用同一个密钥调用任意模型
curl ${CHAT_ENDPOINT} \\
  -H "Authorization: Bearer ah-你的密钥" \\
  -H "Content-Type: application/json" \\
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]}'`
