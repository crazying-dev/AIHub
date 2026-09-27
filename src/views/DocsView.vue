<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import CodeBlock from '../components/CodeBlock.vue'
import { chatSnippets, curlQuickstart, CHAT_ENDPOINT, API_HOST } from '../data/snippets'

const activeSnippet = ref(0)

const toc = [
  { id: 'quickstart', label: '快速开始' },
  { id: 'auth', label: '鉴权方式' },
  { id: 'chat', label: '对话补全接口' },
  { id: 'routing', label: '社区池与模型路由' },
  { id: 'management', label: '管理与社区接口' },
  { id: 'errors', label: '错误码' },
  { id: 'sdk', label: 'SDK 示例' },
]

const params = [
  { name: 'model', type: 'string', required: '是', desc: '模型名称；填 auto 时由社区池按优先级自动选择' },
  { name: 'messages', type: 'array', required: '是', desc: '对话消息列表，支持 system / user / assistant' },
  { name: 'stream', type: 'boolean', required: '否', desc: '是否流式返回，默认 false' },
  { name: 'temperature', type: 'number', required: '否', desc: '采样温度，0~2，默认 1' },
  { name: 'max_tokens', type: 'number', required: '否', desc: '单次响应的最大 token 数' },
]

const routing = [
  {
    title: 'model: auto',
    desc: '整个社区池里挑优先级最高的可用 key：priority 越大越优先，其次已用次数少的、上传更早的。',
  },
  {
    title: '具体模型名',
    desc: '先找上传时填写的 model 名；全部匹配不上，再按上传者给 key 起的名字（name）兜底匹配。',
  },
  {
    title: '次数上限',
    desc: '上传时可设置 maxuse；每次真正打到上游都计一次（失败也计），用满后自动跳过，换下一个候选。',
  },
  {
    title: '协议转换',
    desc: '上游支持 openai / anthropic / gemini；入站支持 OpenAI 与 Anthropic，网关负责双向转换。',
  },
]

const endpoints = [
  { method: 'POST', path: '/api/sign/up/1', desc: '注册第一步：向邮箱发送验证码' },
  { method: 'POST', path: '/api/sign/up/2', desc: '注册第二步：验证码 + 用户名 + 密码创建账号' },
  { method: 'POST', path: '/api/sign', desc: '登录，成功后在 Cookie 中写入 token / id' },
  { method: 'POST', path: '/api/key/new', desc: '新建一个个人 API 密钥' },
  { method: 'POST', path: '/api/key/get', desc: '获取当前用户的个人密钥列表' },
  { method: 'POST', path: '/api/community/upload', desc: '上传自己的上游 key 到社区池，返回 ah-xxxx' },
  { method: 'POST', path: '/api/community/list', desc: '当前用户上传的社区 key（上游密钥已打码）' },
  { method: 'POST', path: '/api/community/delete', desc: '删除自己上传的社区 key' },
  { method: 'POST', path: '/v1/chat/completions', desc: 'OpenAI 协议入站的对话补全接口' },
  { method: 'POST', path: '/v1/messages', desc: 'Anthropic 协议入站的对话补全接口' },
  { method: 'GET', path: '/v1/models', desc: '社区池当前可用的模型标识（含 auto）' },
]

/** 响应示例：放在 script 里而不是模板属性里，避免多行字符串干扰模板解析 */
const responseSample = [
  '{',
  '  "id": "chatcmpl-8f2c1",',
  '  "object": "chat.completion",',
  '  "model": "gpt-4o-mini",',
  '  "choices": [',
  '    {',
  '      "index": 0,',
  '      "message": { "role": "assistant", "content": "你好，我是 AIHub。" },',
  '      "finish_reason": "stop"',
  '    }',
  '  ],',
  '  "usage": { "prompt_tokens": 18, "completion_tokens": 42, "total_tokens": 60 }',
  '}',
].join('\n')

const errors = [
  { code: '401', title: '未授权', desc: '密钥无效、Cookie 过期或验证码错误，检查 Authorization 头或重新登录。' },
  { code: '400', title: '请求格式错误', desc: 'messages 为空或请求体不是 JSON，检查请求体结构。' },
  { code: '502', title: '上游模型错误', desc: '所有候选 key 都调用失败（上游报错 / 超时），无需修改请求，可直接重试。' },
  { code: '503', title: '社区池无可用 key', desc: '没有匹配的可用 key，或候选都已用满调用次数；可上传新 key 或稍后重试。' },
]
</script>

<template>
  <div class="page docs">
    <header class="docs__head">
      <span class="eyebrow">接入文档</span>
      <h1>五分钟把 AIHub 接进你的项目</h1>
      <p>
        AIHub 提供与 OpenAI 完全兼容的 HTTP 接口，任何支持自定义 base_url 的客户端都能直接使用。
      </p>
      <div class="docs__meta">
        <span class="badge"><AppIcon name="globe" :size="13" />{{ API_HOST }}</span>
        <span class="badge"><AppIcon name="code" :size="13" />OpenAI compatible</span>
        <span class="badge badge--ok"><AppIcon name="check" :size="13" />OpenAI / Anthropic 双协议</span>
      </div>
    </header>

    <div class="docs__grid">
      <nav class="toc">
        <span class="toc__title">本页目录</span>
        <a v-for="item in toc" :key="item.id" :href="`#${item.id}`">{{ item.label }}</a>
        <RouterLink class="toc__cta" to="/console">
          去控制台创建密钥
          <AppIcon name="arrow-right" :size="13" />
        </RouterLink>
      </nav>

      <div class="docs__body">
        <section id="quickstart" class="doc-section">
          <h2>快速开始</h2>
          <ol class="steps">
            <li><strong>注册账号</strong><span>使用邮箱接收验证码完成注册。</span></li>
            <li><strong>创建密钥</strong><span>在控制台点击「新建密钥」，得到 <code>ah-</code> 开头的密钥。</span></li>
            <li>
              <strong>上传社区 key</strong>
              <span>在控制台「社区 Key」面板上传自己的上游 key，供整个社区（包括你自己）调度。</span>
            </li>
            <li>
              <strong>发起调用</strong>
              <span>把 OpenAI SDK 的 base_url 换成 <code>{{ API_HOST }}/v1</code>。</span>
            </li>
          </ol>
          <CodeBlock :code="curlQuickstart" label="快速开始" />
        </section>

        <section id="auth" class="doc-section">
          <h2>鉴权方式</h2>
          <p>
            调用 <code>/v1</code> 系列接口时，把密钥放在请求头的 <code>Authorization</code> 中：
          </p>
          <CodeBlock code="Authorization: Bearer ah-your-key" label="HTTP Header" />
          <p class="note">
            <AppIcon name="lock" :size="15" />
            而管理类接口（注册 / 登录 / 密钥管理）使用登录时下发的 HttpOnly Cookie，
            前端不需要也不应该接触 token 内容。
          </p>
        </section>

        <section id="chat" class="doc-section">
          <h2>对话补全接口</h2>
          <p>
            <span class="badge badge--accent">POST</span>
            <code class="endpoint">{{ CHAT_ENDPOINT }}</code>
          </p>
          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr><th>字段</th><th>类型</th><th>必填</th><th>说明</th></tr>
              </thead>
              <tbody>
                <tr v-for="item in params" :key="item.name">
                  <td class="mono">{{ item.name }}</td>
                  <td>{{ item.type }}</td>
                  <td>{{ item.required }}</td>
                  <td class="desc">{{ item.desc }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p>响应体与 OpenAI 保持一致：</p>
          <CodeBlock label="200 OK" :code="responseSample" />
        </section>

        <section id="routing" class="doc-section">
          <h2>社区池与模型路由</h2>
          <p>
            任何登录用户都可以把自己的上游 key 上传到社区池（控制台「社区 Key」面板）。上传后对外暴露的凭证同样是
            <code>ah-</code> 开头的社区密钥，任何人都能用它调用 <code>/v1</code>。
          </p>
          <ul class="endpoints">
            <li v-for="item in routing" :key="item.title">
              <span class="badge badge--accent">{{ item.title }}</span>
              <span class="desc">{{ item.desc }}</span>
            </li>
          </ul>
          <p class="note">
            <AppIcon name="globe" :size="15" />
            网关按候选的上游协议（openai / anthropic / gemini）转换请求与响应，因此上传 Claude 或 Gemini 的
            key，也能用 OpenAI 的 SDK 调用。
          </p>
        </section>

        <section id="management" class="doc-section">
          <h2>管理与社区接口</h2>
          <p>当前后端已实现以下接口（部分仍在开发中，以实际返回为准）：</p>
          <ul class="endpoints">
            <li v-for="item in endpoints" :key="item.path">
              <span class="badge" :class="item.method === 'GET' ? 'badge--ok' : 'badge--accent'">
                {{ item.method }}
              </span>
              <code class="mono">{{ item.path }}</code>
              <span class="desc">{{ item.desc }}</span>
            </li>
          </ul>
        </section>

        <section id="errors" class="doc-section">
          <h2>错误码</h2>
          <div class="errors">
            <article v-for="item in errors" :key="item.code" class="card error">
              <span class="error__code mono">{{ item.code }}</span>
              <h3>{{ item.title }}</h3>
              <p>{{ item.desc }}</p>
            </article>
          </div>
        </section>

        <section id="sdk" class="doc-section">
          <h2>SDK 示例</h2>
          <div class="tabs">
            <button
              v-for="(snippet, index) in chatSnippets"
              :key="snippet.label"
              type="button"
              class="tabs__tab"
              :class="{ 'tabs__tab--active': index === activeSnippet }"
              @click="activeSnippet = index"
            >
              {{ snippet.label }}
            </button>
          </div>
          <CodeBlock
            :code="chatSnippets[activeSnippet].code"
            :label="chatSnippets[activeSnippet].label"
          />
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.docs__head {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-start;
  margin-bottom: 32px;
}

.docs__head p {
  max-width: 62ch;
  font-size: 16px;
}

.docs__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}

.docs__grid {
  display: grid;
  grid-template-columns: 200px minmax(0, 1fr);
  gap: 40px;
  align-items: start;
}

/* 目录 */
.toc {
  position: sticky;
  top: calc(var(--header-h) + 24px);
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-elev);
}

.toc__title {
  font-size: 12px;
  font-weight: 650;
  letter-spacing: 0.08em;
  color: var(--text-soft);
  margin-bottom: 8px;
}

.toc a {
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-size: 14px;
}

.toc a:hover {
  color: var(--accent);
  background: var(--accent-bg);
  text-decoration: none;
}

.toc__cta {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  font-weight: 500;
}

/* 正文 */
.docs__body {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.doc-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 26px;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--bg-elev);
  scroll-margin-top: calc(var(--header-h) + 20px);
}

.doc-section > h2 {
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.doc-section p {
  line-height: 1.7;
}

.steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding-left: 20px;
}

.steps li {
  color: var(--text-muted);
  font-size: 15px;
}

.steps strong {
  display: inline-block;
  min-width: 88px;
  color: var(--text-h);
}

.steps span {
  margin-left: 6px;
}

.note {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  background: var(--info-bg);
  color: var(--info);
  font-size: 13.5px;
}

.endpoint {
  margin-left: 8px;
}

.endpoints {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.endpoints li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-inset);
}

.desc {
  color: var(--text-muted);
  font-size: 14px;
}

.errors {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
}

.error {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: none;
}

.error__code {
  align-self: flex-start;
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--danger-bg);
  color: var(--danger);
  font-size: 13px;
  font-weight: 650;
}

.error p {
  font-size: 13.5px;
}

.tabs {
  display: flex;
  gap: 6px;
}

.tabs__tab {
  padding: 6px 13px;
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  background: var(--bg-elev);
  color: var(--text-muted);
  font: 500 13.5px/1.4 var(--sans);
  cursor: pointer;
}

.tabs__tab--active {
  color: var(--accent);
  background: var(--accent-bg);
  border-color: var(--accent-border);
}

/* 表格 */
.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.table th,
.table td {
  padding: 10px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.table th {
  font-size: 12.5px;
  color: var(--text-soft);
  font-weight: 600;
  background: var(--bg-inset);
}

.table tbody tr:last-child td {
  border-bottom: none;
}

@media (max-width: 900px) {
  .docs__grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .toc {
    position: static;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 6px;
  }

  .toc__title {
    width: 100%;
    margin-bottom: 0;
  }

  .toc__cta {
    margin-top: 6px;
    padding-top: 0;
    border-top: none;
  }
}
</style>
