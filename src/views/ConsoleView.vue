<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import CodeBlock from '../components/CodeBlock.vue'
import { api, HttpError } from '../api/client'
import { session } from '../store/session'
import { toast } from '../store/toast'
import { curlQuickstart } from '../data/snippets'

/** 控制台展示的个人密钥（后端只返回 ah-xxxx 列表） */
interface KeyRow {
  key: string
  label: string
}

const router = useRouter()
const { profile } = session

const loading = ref(true)
const creating = ref(false)
const error = ref('')
const keys = ref<KeyRow[]>([])
const revealed = ref<string[]>([])
const pendingDelete = ref<string | null>(null)
const deleting = ref<string | null>(null)

const keyCount = computed(() => keys.value.length)

function toRow(key: string, index: number): KeyRow {
  return { key, label: index === 0 ? '默认密钥' : `密钥 ${index + 1}` }
}

function mask(key: string): string {
  if (revealed.value.includes(key)) return key
  if (key.length <= 12) return `${key.slice(0, 4)}••••`
  return `${key.slice(0, 7)}••••••••••••${key.slice(-4)}`
}

function toggleReveal(key: string): void {
  revealed.value = revealed.value.includes(key)
    ? revealed.value.filter((item) => item !== key)
    : [...revealed.value, key]
}

async function copyKey(key: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(key)
    toast.ok('密钥已复制到剪贴板')
  } catch {
    toast.error('浏览器拒绝了剪贴板访问，请手动复制')
  }
}

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const list = await api.listKeys()
    keys.value = list.map(toRow)
  } catch (err) {
    if (err instanceof HttpError && err.status === 401) {
      session.signOut()
      toast.error('登录状态已失效，请重新登录')
      await router.push({ name: 'login', query: { redirect: '/console' } })
      return
    }
    error.value = err instanceof Error ? err.message : '密钥列表加载失败'
  } finally {
    loading.value = false
  }
}

async function createKey(): Promise<void> {
  creating.value = true
  try {
    await api.createKey()
    await load()
    toast.ok('密钥创建成功')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '创建密钥失败')
  } finally {
    creating.value = false
  }
}

/** 两步吊销：第一次点垃圾桶进入待确认，再点「确认吊销」才真正删除 */
async function removeKey(key: string): Promise<void> {
  deleting.value = key
  try {
    await api.deleteKey(key)
    toast.ok('密钥已吊销')
    await load()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '吊销失败')
  } finally {
    deleting.value = null
    pendingDelete.value = null
  }
}

onMounted(load)
</script>

<template>
  <div class="page console">
    <header class="console__head">
      <div>
        <span class="eyebrow">控制台</span>
        <h1 class="console__title">你好，{{ profile?.name || '开发者' }}</h1>
        <p>管理你的 API 密钥。密钥用于调用 <code>/v1</code>，实际由社区池里的上游 key 提供模型能力。</p>
      </div>
      <div class="console__head-actions">
        <button class="btn" type="button" @click="load">
          <AppIcon name="clock" :size="16" />
          刷新
        </button>
        <button class="btn btn--primary" type="button" :disabled="creating" @click="createKey">
          <AppIcon name="plus" :size="16" />
          {{ creating ? '创建中…' : '新建密钥' }}
        </button>
      </div>
    </header>

    <p v-if="error" class="alert alert--error">
      <AppIcon name="alert" :size="15" />
      {{ error }}
      <button class="btn btn--sm" type="button" @click="load">重试</button>
    </p>

    <div class="console__grid">
      <section class="card keys">
        <div class="card__head">
          <div>
            <h3>API 密钥</h3>
            <p class="keys__count">共 {{ keyCount }} 个，用于调用 /v1 接口</p>
          </div>
          <span class="badge">ah- 前缀</span>
        </div>

        <div v-if="loading" class="keys__list">
          <div v-for="n in 2" :key="n" class="skeleton keys__skeleton" />
        </div>

        <div v-else-if="!keys.length" class="keys__empty">
          <AppIcon name="lock" :size="22" />
          <h3>还没有密钥</h3>
          <p>创建一个密钥，即可开始调用 /v1。</p>
          <button class="btn btn--primary" type="button" @click="createKey">
            <AppIcon name="plus" :size="16" />
            新建密钥
          </button>
        </div>

        <ul v-else class="keys__list">
          <li v-for="item in keys" :key="item.key" class="key-row">
            <div class="key-row__main">
              <div class="key-row__title">
                <strong>{{ item.label }}</strong>
              </div>
              <code class="key-row__value">{{ mask(item.key) }}</code>
              <div class="key-row__meta">
                <span>调用时放在 Authorization: Bearer &lt;key&gt;</span>
              </div>
            </div>
            <div class="key-row__actions">
              <template v-if="pendingDelete === item.key">
                <button
                  class="btn btn--sm btn--danger"
                  type="button"
                  :disabled="deleting === item.key"
                  @click="removeKey(item.key)"
                >
                  {{ deleting === item.key ? '吊销中…' : '确认吊销' }}
                </button>
                <button class="btn btn--sm" type="button" @click="pendingDelete = null">取消</button>
              </template>
              <template v-else>
                <button
                  class="icon-btn"
                  type="button"
                  :title="revealed.includes(item.key) ? '隐藏' : '显示'"
                  @click="toggleReveal(item.key)"
                >
                  <AppIcon :name="revealed.includes(item.key) ? 'eye-off' : 'eye'" :size="16" />
                </button>
                <button class="icon-btn" type="button" title="复制" @click="copyKey(item.key)">
                  <AppIcon name="copy" :size="15" />
                </button>
                <button
                  class="icon-btn icon-btn--danger"
                  type="button"
                  title="吊销密钥"
                  @click="pendingDelete = item.key"
                >
                  <AppIcon name="trash" :size="15" />
                </button>
              </template>
            </div>
          </li>
        </ul>
      </section>

      <aside class="console__side">
        <section class="card">
          <div class="card__head">
            <h3>社区池</h3>
            <RouterLink class="quick__link" to="/community">
              前往社区
              <AppIcon name="arrow-right" :size="13" />
            </RouterLink>
          </div>
          <div class="card__body">
            <p class="side__text">
              社区池汇集了大家上传的上游 key，你的 <code>ah-</code> 密钥会按
              <code>model</code> 自动路由过去。<code>model: auto</code> 时优先选择优先级更高的 key。
            </p>
          </div>
        </section>

        <section class="card">
          <div class="card__head">
            <h3>快速开始</h3>
            <RouterLink class="quick__link" to="/docs">
              完整文档
              <AppIcon name="arrow-right" :size="13" />
            </RouterLink>
          </div>
          <div class="card__body">
            <CodeBlock :code="curlQuickstart" label="cURL" />
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.console {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.console__head {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  align-items: flex-end;
  justify-content: space-between;
}

.console__title {
  margin: 6px 0 4px;
  font-size: 30px;
}

.console__head-actions {
  display: flex;
  gap: 10px;
}

/* 主体两栏 */
.console__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.console__side {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.side__text {
  font-size: 14.5px;
  line-height: 1.7;
}

.keys__count {
  margin-top: 4px;
  font-size: 13px;
  color: var(--text-soft);
}

.keys__list {
  list-style: none;
  margin: 0;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.keys__skeleton {
  height: 84px;
}

.keys__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 46px 24px;
  text-align: center;
  color: var(--text-soft);
}

.keys__empty h3 {
  color: var(--text-h);
}

.keys__empty .btn {
  margin-top: 10px;
}

.key-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-inset);
  transition: border-color 0.16s ease, background 0.16s ease;
}

.key-row:hover {
  border-color: var(--accent-border);
  background: var(--bg-elev);
}

.key-row__main {
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 0;
  flex: 1 1 auto;
}

.key-row__title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.key-row__value {
  align-self: flex-start;
  max-width: 100%;
  overflow-x: auto;
  white-space: nowrap;
  background: var(--code-bg);
  color: var(--code-text);
}

.key-row__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  font-size: 12.5px;
  color: var(--text-soft);
}

.key-row__actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.icon-btn {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.16s ease, background 0.16s ease;
}

.icon-btn:hover:not(:disabled) {
  color: var(--text-h);
  background: var(--bg-soft);
}

.icon-btn--danger:hover:not(:disabled) {
  color: var(--danger);
}

.quick__link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

@media (max-width: 960px) {
  .console__grid {
    grid-template-columns: 1fr;
  }
}
</style>