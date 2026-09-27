<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import CodeBlock from '../components/CodeBlock.vue'
import { api, HttpError, withDemo } from '../api/client'
import { demo } from '../store/demo'
import { demoKeys, demoLogs, demoStats } from '../api/mock'
import type { ApiKeyItem, StatItem } from '../api/mock'
import { session } from '../store/session'
import { toast } from '../store/toast'
import { curlQuickstart } from '../data/snippets'

const router = useRouter()
const { profile } = session

const loading = ref(true)
const creating = ref(false)
const error = ref('')
const keys = ref<ApiKeyItem[]>([])
const revealed = ref<string[]>([])

const stats = ref<StatItem[]>(demoStats)
const logs = demoLogs

/** 用量趋势（后端统计接口尚未完成，先用演示柱状数据） */
const trend = [32, 48, 41, 66, 58, 74, 69, 88, 76, 94, 82, 100]
const trendMax = Math.max(...trend)

const keyCount = computed(() => keys.value.length)

function toItem(key: string, index: number): ApiKeyItem {
  return {
    key,
    label: index === 0 ? '默认密钥' : `密钥 ${index + 1}`,
    createdAt: '—',
    lastUsed: '—',
    status: 'active',
  }
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
    keys.value = await withDemo(
      () => api.listKeys().then((list) => list.map(toItem)),
      () => demoKeys,
    )
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
    await withDemo(
      () => api.createKey(),
      () => undefined,
    )
    await load()
    toast.ok(demo.active.value ? '已生成演示密钥（未连接后端）' : '密钥创建成功')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '创建密钥失败')
  } finally {
    creating.value = false
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
        <p>管理你的 API 密钥，并查看最近的调用情况。</p>
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

    <section class="stats">
      <article v-for="item in stats" :key="item.label" class="card stat">
        <span class="stat__label">{{ item.label }}</span>
        <strong class="stat__value">{{ item.value }}</strong>
        <span class="badge" :class="`badge--${item.tone}`">{{ item.delta }}</span>
      </article>
    </section>

    <p v-if="error" class="alert alert--error">
      <AppIcon name="alert" :size="15" />
      {{ error }}
    </p>

    <div class="console__grid">
      <section class="card keys">
        <div class="card__head">
          <div>
            <h3>API 密钥</h3>
            <p class="keys__count">共 {{ keyCount }} 个，用于调用 /v1 接口</p>
          </div>
          <span class="badge"> ah- 前缀</span>
        </div>

        <div v-if="loading" class="keys__list">
          <div v-for="n in 2" :key="n" class="skeleton keys__skeleton" />
        </div>

        <div v-else-if="!keys.length" class="keys__empty">
          <AppIcon name="lock" :size="22" />
          <h3>还没有密钥</h3>
          <p>创建一个密钥，即可开始调用全部模型。</p>
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
                <span class="badge" :class="item.status === 'active' ? 'badge--ok' : 'badge--warn'">
                  {{ item.status === 'active' ? '启用中' : '已停用' }}
                </span>
              </div>
              <code class="key-row__value">{{ mask(item.key) }}</code>
              <div class="key-row__meta">
                <span>创建：{{ item.createdAt }}</span>
                <span>最近使用：{{ item.lastUsed }}</span>
              </div>
            </div>
            <div class="key-row__actions">
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
              <button class="icon-btn icon-btn--danger" type="button" title="吊销（后端接口待实现）" disabled>
                <AppIcon name="trash" :size="15" />
              </button>
            </div>
          </li>
        </ul>
      </section>

      <aside class="console__side">
        <section class="card">
          <div class="card__head">
            <h3>用量趋势</h3>
            <span class="badge badge--accent">近 12 周</span>
          </div>
          <div class="card__body">
            <div class="chart">
              <span
                v-for="(value, index) in trend"
                :key="index"
                class="chart__bar"
                :style="{ height: `${Math.round((value / trendMax) * 100)}%` }"
              />
            </div>
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

    <section class="card">
      <div class="card__head">
        <h3>最近调用</h3>
        <span class="badge">演示数据</span>
      </div>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>请求 ID</th>
              <th>模型</th>
              <th>Tokens</th>
              <th>延迟</th>
              <th>状态</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in logs" :key="row.id">
              <td class="mono">{{ row.id }}</td>
              <td class="mono">{{ row.model }}</td>
              <td>{{ row.tokens ? row.tokens.toLocaleString() : '—' }}</td>
              <td>{{ row.latency ? `${row.latency} ms` : '—' }}</td>
              <td>
                <span class="badge" :class="row.status === 'ok' ? 'badge--ok' : 'badge--danger'">
                  {{ row.status === 'ok' ? '成功' : '失败' }}
                </span>
              </td>
              <td class="mono">{{ row.ts }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
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

/* 概览卡片 */
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
  padding: 18px 20px;
}

.stat__label {
  font-size: 13px;
  color: var(--text-muted);
}

.stat__value {
  font-size: 26px;
  font-weight: 680;
  color: var(--text-h);
  font-variant-numeric: tabular-nums;
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
  gap: 4px;
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

.icon-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.icon-btn--danger:hover:not(:disabled) {
  color: var(--danger);
}

/* 迷你柱状图 */
.chart {
  display: flex;
  align-items: flex-end;
  gap: 5px;
  height: 120px;
}

.chart__bar {
  flex: 1 1 0;
  min-height: 6px;
  border-radius: 4px 4px 2px 2px;
  background: linear-gradient(180deg, var(--accent), color-mix(in srgb, var(--accent) 35%, transparent));
}

.quick__link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

/* 表格 */
.table-wrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.table th,
.table td {
  padding: 12px 22px;
  text-align: left;
  white-space: nowrap;
  border-bottom: 1px solid var(--border);
}

.table th {
  font-size: 12.5px;
  font-weight: 600;
  letter-spacing: 0.03em;
  color: var(--text-soft);
  background: var(--bg-inset);
}

.table tbody tr:last-child td {
  border-bottom: none;
}

.table tbody tr:hover td {
  background: var(--bg-inset);
}

@media (max-width: 960px) {
  .console__grid {
    grid-template-columns: 1fr;
  }
}
</style>
