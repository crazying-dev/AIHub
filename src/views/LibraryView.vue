<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import { api } from '../api/client'
import type { PrivateKeyItem } from '../api/types'
import { toast } from '../store/toast'

/**
 * 私有库页：上传 / 管理只给自己用的上游 key。
 *
 * 对应后端 route/api/private.py：
 * - POST /api/private/list   当前用户私有库全部条目
 * - POST /api/private/upload 上传自己的上游 key
 * - POST /api/private/delete 删除某条 key
 *
 * 谁能用到它们：你在「控制台」创建的个人密钥 ah-<id>；并且要落在该密钥的「授权范围」里
 * （一条都不勾选 = 可以使用私有库全部 key）。公共库的固定凭证 ah-xxxx 碰不到私有库。
 */
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const items = ref<PrivateKeyItem[]>([])
const formOpen = ref(false)
const pendingDelete = ref<string | null>(null)
const deleting = ref<string | null>(null)

const protocols = [
  { value: 'openai', label: 'OpenAI 兼容' },
  { value: 'anthropic', label: 'Anthropic / Claude' },
  { value: 'gemini', label: 'Google Gemini' },
]

const form = reactive({
  url: '',
  key: '',
  model: '',
  protocol: 'openai',
  name: '',
  priority: 50,
  maxuse: '',
  text: '',
})

function percent(item: PrivateKeyItem): number {
  if (!item.maxuse) return 0
  return Math.min(100, Math.round((item.used / item.maxuse) * 100))
}

function usageText(item: PrivateKeyItem): string {
  if (item.maxuse === null) return `${item.used} 次 / 不限`
  return `${item.used} / ${item.maxuse} 次`
}

function healthy(item: PrivateKeyItem): boolean {
  return item.enabled && (item.remaining === null || item.remaining > 0)
}

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    items.value = await api.listPrivateKeys()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '私有库加载失败'
  } finally {
    loading.value = false
  }
}

function toggleForm(): void {
  formOpen.value = !formOpen.value
}

async function submit(): Promise<void> {
  if (!form.url.trim() || !form.key.trim() || !form.model.trim()) {
    toast.error('上游地址、上游密钥、模型名均为必填')
    return
  }
  saving.value = true
  try {
    await api.uploadPrivateKey({
      url: form.url.trim(),
      key: form.key.trim(),
      model: form.model.trim(),
      protocol: form.protocol,
      name: form.name.trim() || undefined,
      priority: Number(form.priority) || 50,
      maxuse: form.maxuse === '' ? null : Number(form.maxuse),
      text: form.text.trim() || undefined,
    })
    toast.ok('上传成功，已加入私有库')
    form.key = ''
    await load()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '上传失败')
  } finally {
    saving.value = false
  }
}

async function remove(item: PrivateKeyItem): Promise<void> {
  deleting.value = item.id
  try {
    await api.deletePrivateKey(item.id)
    toast.ok('已从私有库删除')
    await load()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '删除失败')
  } finally {
    deleting.value = null
    pendingDelete.value = null
  }
}

onMounted(load)
</script>

<template>
  <div class="page library">
    <header class="library__head">
      <div>
        <span class="eyebrow">私有库</span>
        <h1 class="library__title">只给自己用的上游 key</h1>
        <p class="library__lead">
          私有库里的 key 只有你自己的个人密钥 <code>ah-&lt;id&gt;</code> 能调度，
          而且还要落在该密钥的「授权范围」里。公共库的 <code>ah-xxxx</code> 完全碰不到这里。
        </p>
      </div>
      <div class="library__head-actions">
        <button class="btn" type="button" @click="load">
          <AppIcon name="clock" :size="16" />
          刷新
        </button>
        <button class="btn btn--primary" type="button" @click="toggleForm">
          <AppIcon :name="formOpen ? 'close' : 'plus'" :size="16" />
          {{ formOpen ? '收起' : '上传上游 Key' }}
        </button>
      </div>
    </header>

    <p class="alert alert--info library__tip">
      <AppIcon name="lock" :size="15" />
      <span>
        想限定某条个人密钥只能用其中几条？去
        <RouterLink to="/console">控制台</RouterLink>
        点它的「授权范围」勾选即可；一条都不勾选表示可以使用全部私有 key。
      </span>
    </p>

    <form v-if="formOpen" class="card library__form" @submit.prevent="submit">
      <div class="library__form-grid">
        <label class="field">
          <span class="field__label">上游地址 base_url <i>*</i></span>
          <input v-model="form.url" class="input input--mono" placeholder="https://api.openai.com/v1" />
          <span class="field__hint">只填到 /v1，不要带 /chat/completions</span>
        </label>
        <label class="field">
          <span class="field__label">上游密钥 <i>*</i></span>
          <input v-model="form.key" class="input input--mono" type="password" placeholder="sk-..." />
          <span class="field__hint">只用于转发，列表里只显示打码结果</span>
        </label>
        <label class="field">
          <span class="field__label">上游协议 <i>*</i></span>
          <select v-model="form.protocol" class="select">
            <option v-for="item in protocols" :key="item.value" :value="item.value">
              {{ item.label }}
            </option>
          </select>
          <span class="field__hint">网关会把入站请求转换成这个协议</span>
        </label>
        <label class="field">
          <span class="field__label">模型名 <i>*</i></span>
          <input v-model="form.model" class="input input--mono" placeholder="gpt-4o-mini" />
          <span class="field__hint">你的密钥填这个名字（或 auto）就会路由到这条 key</span>
        </label>
        <label class="field">
          <span class="field__label">命名（可选）</span>
          <input v-model="form.name" class="input" placeholder="例如：生产环境" />
          <span class="field__hint">模型名都匹配不上时，按这个命名兜底匹配</span>
        </label>
        <label class="field">
          <span class="field__label">优先级</span>
          <input v-model="form.priority" class="input" type="number" min="1" max="100" />
          <span class="field__hint">数字越大越优先（默认 50）</span>
        </label>
        <label class="field">
          <span class="field__label">调用次数上限（可选）</span>
          <input v-model="form.maxuse" class="input" type="number" min="0" placeholder="留空 = 不限" />
          <span class="field__hint">每次真正打到上游就计一次，用满后自动跳过</span>
        </label>
        <label class="field">
          <span class="field__label">备注（可选）</span>
          <input v-model="form.text" class="input" placeholder="给自己的说明" />
        </label>
      </div>
      <div class="row row--between library__submit">
        <span class="muted">上传后可随时删除，只会影响这一条 key。</span>
        <button class="btn btn--primary" type="submit" :disabled="saving">
          <AppIcon name="plus" :size="16" />
          {{ saving ? '上传中…' : '上传到私有库' }}
        </button>
      </div>
    </form>

    <p v-if="error" class="alert alert--error">
      <AppIcon name="alert" :size="15" />
      {{ error }}
      <button class="btn btn--sm" type="button" @click="load">重试</button>
    </p>

    <div class="library__bar">
      <span class="badge"><AppIcon name="lock" :size="12" />共 {{ items.length }} 条</span>
      <RouterLink class="library__link" to="/console">
        去控制台管理授权范围
        <AppIcon name="arrow-right" :size="13" />
      </RouterLink>
    </div>

    <div v-if="loading" class="library__list">
      <div v-for="n in 3" :key="n" class="skeleton library__skeleton" />
    </div>

    <div v-else-if="!items.length" class="card library__empty">
      <AppIcon name="lock" :size="22" />
      <h3>私有库还是空的</h3>
      <p>上传第一条上游 key，它只会被你的个人密钥调度。</p>
    </div>

    <ul v-else class="library__list">
      <li v-for="item in items" :key="item.id" class="crow">
        <div class="crow__main">
          <div class="crow__title">
            <strong>{{ item.name || item.model }}</strong>
            <span class="badge badge--accent">{{ item.protocol }}</span>
            <span class="badge" :class="healthy(item) ? 'badge--ok' : 'badge--warn'">
              {{ !item.enabled ? '已停用' : healthy(item) ? '可用' : '已用满' }}
            </span>
            <span class="badge">优先级 {{ item.priority }}</span>
          </div>
          <code class="crow__value">{{ item.key }}</code>
          <div class="crow__meta">
            <span>模型 <code>{{ item.model }}</code></span>
            <span>上游 {{ item.url }}</span>
            <span v-if="item.text">{{ item.text }}</span>
          </div>
          <div class="crow__usage">
            <div class="bar"><span class="bar__fill" :style="{ width: `${percent(item)}%` }" /></div>
            <span class="crow__count">{{ usageText(item) }}</span>
          </div>
        </div>
        <div class="crow__actions">
          <template v-if="pendingDelete === item.id">
            <button
              class="btn btn--sm btn--danger"
              type="button"
              :disabled="deleting === item.id"
              @click="remove(item)"
            >
              {{ deleting === item.id ? '删除中…' : '确认删除' }}
            </button>
            <button class="btn btn--sm" type="button" @click="pendingDelete = null">取消</button>
          </template>
          <template v-else>
            <button
              class="icon-btn icon-btn--danger"
              type="button"
              title="删除这条 key"
              @click="pendingDelete = item.id"
            >
              <AppIcon name="trash" :size="15" />
            </button>
          </template>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.library {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.library__head {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  align-items: flex-end;
  justify-content: space-between;
}

.library__title {
  margin: 6px 0 6px;
  font-size: 30px;
}

.library__lead {
  max-width: 66ch;
  line-height: 1.7;
}

.library__head-actions {
  display: flex;
  gap: 10px;
}

.library__tip {
  align-items: center;
}

.library__form {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.library__form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.library__submit {
  gap: 12px;
  flex-wrap: wrap;
}

.field__label i {
  color: var(--danger);
  font-style: normal;
  margin-left: 3px;
}

.library__bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.library__link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
}

.library__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.library__skeleton {
  height: 104px;
}

.library__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 46px 24px;
  text-align: center;
  color: var(--text-soft);
}

.library__empty h3 {
  color: var(--text-h);
}

.crow {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px 18px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-elev);
  transition: border-color 0.16s ease, background 0.16s ease;
}

.crow:hover {
  border-color: var(--accent-border);
}

.crow__main {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  flex: 1 1 auto;
}

.crow__title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.crow__value {
  align-self: flex-start;
  max-width: 100%;
  overflow-x: auto;
  white-space: nowrap;
  background: var(--code-bg);
  color: var(--code-text);
}

.crow__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  font-size: 12.5px;
  color: var(--text-soft);
}

.crow__usage {
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: 320px;
}

.bar {
  flex: 1 1 auto;
  height: 6px;
  border-radius: 999px;
  background: var(--bg-soft);
  overflow: hidden;
}

.bar__fill {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--accent), var(--brand-2));
}

.crow__count {
  font-size: 12.5px;
  color: var(--text-muted);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.crow__actions {
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

@media (max-width: 720px) {
  .library__form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
