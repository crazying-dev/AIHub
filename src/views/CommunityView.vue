<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import { api } from '../api/client'
import type { CommunityKeyItem } from '../api/types'
import { session } from '../store/session'
import { toast } from '../store/toast'

/**
 * 社区页：浏览 / 上传 / 删除社区池里的上游 key。
 *
 * 对应后端 route/api/community.py：
 * - POST /api/community/pool   公开浏览全部条目（登录后自己上传的条目 mine = true）
 * - POST /api/community/upload 登录后上传自己的上游 key，返回 ah-xxxx
 * - POST /api/community/delete 删除自己上传的条目
 */
const router = useRouter()
const { isAuthed } = session

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const items = ref<CommunityKeyItem[]>([])
const formOpen = ref(false)
const issued = ref('')
const filter = ref<'all' | 'mine'>('all')
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

const mineCount = computed(() => items.value.filter((item) => item.mine).length)

const visible = computed(() =>
  filter.value === 'mine' ? items.value.filter((item) => item.mine) : items.value,
)

function percent(item: CommunityKeyItem): number {
  if (!item.maxuse) return 0
  return Math.min(100, Math.round((item.used / item.maxuse) * 100))
}

function usageText(item: CommunityKeyItem): string {
  if (item.maxuse === null) return `${item.used} 次 / 不限`
  return `${item.used} / ${item.maxuse} 次`
}

function healthy(item: CommunityKeyItem): boolean {
  return item.enabled && (item.remaining === null || item.remaining > 0)
}

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    items.value = await api.listCommunityPool()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '社区池加载失败'
  } finally {
    loading.value = false
  }
}

function toggleForm(): void {
  // 未登录先引导登录，登录后回到本页
  if (!isAuthed.value && !formOpen.value) {
    toast.info('登录后即可上传自己的上游 key')
    void router.push({ name: 'login', query: { redirect: '/community' } })
    return
  }
  formOpen.value = !formOpen.value
}

async function submit(): Promise<void> {
  if (!form.url.trim() || !form.key.trim() || !form.model.trim()) {
    toast.error('上游地址、上游密钥、模型名均为必填')
    return
  }
  saving.value = true
  try {
    issued.value = await api.uploadCommunityKey({
      url: form.url.trim(),
      key: form.key.trim(),
      model: form.model.trim(),
      protocol: form.protocol,
      name: form.name.trim() || undefined,
      priority: Number(form.priority) || 50,
      maxuse: form.maxuse === '' ? null : Number(form.maxuse),
      text: form.text.trim() || undefined,
    })
    toast.ok('上传成功，已加入社区池')
    form.key = ''
    await load()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '上传失败')
  } finally {
    saving.value = false
  }
}

async function remove(item: CommunityKeyItem): Promise<void> {
  deleting.value = item.id
  try {
    await api.deleteCommunityKey(item.id)
    if (issued.value === `ah-${item.id}`) issued.value = ''
    toast.ok('已从社区池删除')
    await load()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '删除失败')
  } finally {
    deleting.value = null
    pendingDelete.value = null
  }
}

async function copy(value: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(value)
    toast.ok('已复制到剪贴板')
  } catch {
    toast.error('浏览器拒绝了剪贴板访问，请手动复制')
  }
}

onMounted(load)
</script>

<template>
  <div class="page community">
    <header class="community__head">
      <div>
        <span class="eyebrow">社区</span>
        <h1 class="community__title">社区池</h1>
        <p class="community__lead">
          这里汇集社区成员上传的上游 key。任何人都能用自己的 <code>ah-</code> 密钥调用
          <code>/v1</code>，<code>model: auto</code> 时按优先级自动挑一条可用 key。
        </p>
      </div>
      <div class="community__head-actions">
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

    <p v-if="issued" class="alert alert--ok community__issued">
      <AppIcon name="check" :size="15" />
      <span>上传成功，你的社区密钥：<code>{{ issued }}</code></span>
      <button class="btn btn--sm" type="button" @click="copy(issued)">复制</button>
    </p>

    <form v-if="formOpen && isAuthed" class="card community__form" @submit.prevent="submit">
      <div class="community__form-grid">
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
          <span class="field__hint">调用方填这个名字（或 auto）就会路由到这条 key</span>
        </label>
        <label class="field">
          <span class="field__label">命名（可选）</span>
          <input v-model="form.name" class="input" placeholder="例如：长文翻译" />
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
      <div class="row row--between community__submit">
        <span class="muted">上传后可随时删除，只会影响这一条 key。</span>
        <button class="btn btn--primary" type="submit" :disabled="saving">
          <AppIcon name="plus" :size="16" />
          {{ saving ? '上传中…' : '上传到社区池' }}
        </button>
      </div>
    </form>

    <p v-if="error" class="alert alert--error">
      <AppIcon name="alert" :size="15" />
      {{ error }}
      <button class="btn btn--sm" type="button" @click="load">重试</button>
    </p>

    <div class="community__bar">
      <div class="community__filters">
        <button
          type="button"
          class="filter"
          :class="{ 'filter--active': filter === 'all' }"
          @click="filter = 'all'"
        >
          全部 · {{ items.length }}
        </button>
        <button
          v-if="isAuthed"
          type="button"
          class="filter"
          :class="{ 'filter--active': filter === 'mine' }"
          @click="filter = 'mine'"
        >
          我上传的 · {{ mineCount }}
        </button>
      </div>
      <RouterLink v-if="!isAuthed" class="community__login" to="/login">
        登录后可上传与管理自己的 key
        <AppIcon name="arrow-right" :size="13" />
      </RouterLink>
    </div>

    <div v-if="loading" class="community__list">
      <div v-for="n in 3" :key="n" class="skeleton community__skeleton" />
    </div>

    <div v-else-if="!visible.length" class="card community__empty">
      <AppIcon name="globe" :size="22" />
      <h3>{{ filter === 'mine' ? '你还没有上传过 key' : '社区池还是空的' }}</h3>
      <p>上传第一条上游 key，所有人就都能用它调用 /v1。</p>
    </div>

    <ul v-else class="community__list">
      <li v-for="item in visible" :key="item.id" class="crow">
        <div class="crow__main">
          <div class="crow__title">
            <strong>{{ item.name || item.model }}</strong>
            <span class="badge badge--accent">{{ item.protocol }}</span>
            <span class="badge" :class="healthy(item) ? 'badge--ok' : 'badge--warn'">
              {{ !item.enabled ? '已停用' : healthy(item) ? '可用' : '已用满' }}
            </span>
            <span class="badge">优先级 {{ item.priority }}</span>
            <span v-if="item.mine" class="badge badge--ok">我上传的</span>
          </div>
          <code class="crow__value">{{ item.key }}</code>
          <div class="crow__meta">
            <span>模型 <code>{{ item.model }}</code></span>
            <span>上游 {{ item.url }}</span>
            <span v-if="item.mine">社区密钥 <code>ah-{{ item.id }}</code></span>
            <span v-if="item.text">{{ item.text }}</span>
          </div>
          <div class="crow__usage">
            <div class="bar"><span class="bar__fill" :style="{ width: `${percent(item)}%` }" /></div>
            <span class="crow__count">{{ usageText(item) }}</span>
          </div>
        </div>
        <div class="crow__actions">
          <template v-if="item.mine">
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
              <button class="icon-btn" type="button" title="复制社区密钥" @click="copy(`ah-${item.id}`)">
                <AppIcon name="copy" :size="15" />
              </button>
              <button
                class="icon-btn icon-btn--danger"
                type="button"
                title="删除这条 key"
                @click="pendingDelete = item.id"
              >
                <AppIcon name="trash" :size="15" />
              </button>
            </template>
          </template>
          <span v-else class="crow__owner">他人上传</span>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.community {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.community__head {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  align-items: flex-end;
  justify-content: space-between;
}

.community__title {
  margin: 6px 0 6px;
  font-size: 30px;
}

.community__lead {
  max-width: 66ch;
  line-height: 1.7;
}

.community__head-actions {
  display: flex;
  gap: 10px;
}

.community__issued {
  align-items: center;
}

.community__issued code {
  margin: 0 4px;
}

.community__form {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.community__form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.community__submit {
  gap: 12px;
  flex-wrap: wrap;
}

.field__label i {
  color: var(--danger);
  font-style: normal;
  margin-left: 3px;
}

.community__bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.community__filters {
  display: flex;
  gap: 8px;
}

.filter {
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  background: var(--bg-elev);
  color: var(--text-muted);
  font: 500 13.5px/1.4 var(--sans);
  cursor: pointer;
  transition: color 0.16s ease, background 0.16s ease, border-color 0.16s ease;
}

.filter:hover {
  color: var(--text-h);
}

.filter--active {
  color: var(--accent);
  background: var(--accent-bg);
  border-color: var(--accent-border);
}

.community__login {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
}

.community__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.community__skeleton {
  height: 104px;
}

.community__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 46px 24px;
  text-align: center;
  color: var(--text-soft);
}

.community__empty h3 {
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

.crow__owner {
  font-size: 12.5px;
  color: var(--text-soft);
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
  .community__form-grid {
    grid-template-columns: 1fr;
  }
}
</style>