<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from './AppIcon.vue'
import { api, HttpError, withDemo } from '../api/client'
import { demo } from '../store/demo'
import { demoCommunityKeys } from '../api/mock'
import type { CommunityKeyItem } from '../api/mock'
import { session } from '../store/session'
import { toast } from '../store/toast'

/**
 * 社区 Key 面板。
 *
 * 对应后端 route/api/community.py：任何登录用户都可以把自己的上游 key 上传进社区池，
 * 上传后对外暴露为 ah-xxxx 的社区密钥，池内按 priority 排序供 /v1 调度。
 */
const router = useRouter()

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const items = ref<CommunityKeyItem[]>([])
const formOpen = ref(false)
const issued = ref('')

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

const filled = computed(() => items.value.length > 0)

function percent(item: CommunityKeyItem): number {
  if (!item.maxuse) return 0
  return Math.min(100, Math.round((item.used / item.maxuse) * 100))
}

function usageText(item: CommunityKeyItem): string {
  return item.maxuse === null ? `${item.used} 次 / 不限` : `${item.used} / ${item.maxuse} 次`
}

function healthy(item: CommunityKeyItem): boolean {
  return item.enabled && (item.remaining === null || item.remaining > 0)
}

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    items.value = await withDemo(
      () => api.listCommunityKeys(),
      () => demoCommunityKeys,
    )
  } catch (err) {
    if (err instanceof HttpError && err.status === 401) {
      session.signOut()
      toast.error('登录状态已失效，请重新登录')
      await router.push({ name: 'login', query: { redirect: '/console' } })
      return
    }
    error.value = err instanceof Error ? err.message : '社区密钥加载失败'
  } finally {
    loading.value = false
  }
}

async function submit(): Promise<void> {
  if (!form.url.trim() || !form.key.trim() || !form.model.trim()) {
    toast.error('上游地址、上游密钥、模型名均为必填')
    return
  }
  saving.value = true
  try {
    const created = await withDemo(
      () =>
        api.uploadCommunityKey({
          url: form.url.trim(),
          key: form.key.trim(),
          model: form.model.trim(),
          protocol: form.protocol,
          name: form.name.trim() || undefined,
          priority: Number(form.priority) || 50,
          maxuse: form.maxuse === '' ? null : Number(form.maxuse),
          text: form.text.trim() || undefined,
        }),
      () => `ah-demo-${Date.now()}`,
    )
    issued.value = created
    toast.ok(demo.active.value ? '已生成演示社区密钥（未连接后端）' : '上传成功，已加入社区池')
    form.key = ''
    await load()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '上传失败')
  } finally {
    saving.value = false
  }
}

async function remove(item: CommunityKeyItem): Promise<void> {
  try {
    await withDemo(
      () => api.deleteCommunityKey(item.id),
      () => undefined,
    )
    if (issued.value === `ah-${item.id}`) issued.value = ''
    toast.ok('已从社区池删除')
    await load()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '删除失败')
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
  <section class="card community">
    <div class="card__head community__head">
      <div>
        <h3>社区 Key</h3>
        <p class="community__sub">
          上传你自己的上游 key，对外暴露为 <code>ah-</code> 开头的社区密钥，任何人都能用它调用
          <code>/v1</code>；<code>model: auto</code> 时会按优先级自动挑一条。
        </p>
      </div>
      <div class="community__actions">
        <button class="btn" type="button" @click="load">
          <AppIcon name="clock" :size="16" />
          刷新
        </button>
        <button class="btn btn--primary" type="button" @click="formOpen = !formOpen">
          <AppIcon :name="formOpen ? 'close' : 'plus'" :size="16" />
          {{ formOpen ? '收起' : '上传 Key' }}
        </button>
      </div>
    </div>

    <p v-if="issued" class="alert alert--ok community__issued">
      <AppIcon name="check" :size="15" />
      <span>上传成功，社区密钥：<code>{{ issued }}</code></span>
      <button class="btn btn--sm" type="button" @click="copy(issued)">复制</button>
    </p>

    <form v-if="formOpen" class="community__form" @submit.prevent="submit">
      <div class="grid-2">
        <label class="field">
          <span class="field__label">上游地址 base_url<i>*</i></span>
          <input v-model="form.url" class="input input--mono" placeholder="https://api.openai.com/v1" />
          <span class="field__hint">只填到 /v1，不要带 /chat/completions</span>
        </label>
        <label class="field">
          <span class="field__label">上游密钥<i>*</i></span>
          <input v-model="form.key" class="input input--mono" type="password" placeholder="sk-..." />
          <span class="field__hint">只用于转发，列表里只显示打码结果</span>
        </label>
        <label class="field">
          <span class="field__label">上游协议<i>*</i></span>
          <select v-model="form.protocol" class="select">
            <option v-for="item in protocols" :key="item.value" :value="item.value">
              {{ item.label }}
            </option>
          </select>
          <span class="field__hint">网关会把入站请求转换成这个协议</span>
        </label>
        <label class="field">
          <span class="field__label">模型名<i>*</i></span>
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
    </p>

    <div v-if="loading" class="community__list">
      <div v-for="n in 2" :key="n" class="skeleton community__skeleton" />
    </div>

    <div v-else-if="!filled" class="community__empty">
      <AppIcon name="globe" :size="22" />
      <h3>社区池还是空的</h3>
      <p>上传第一条上游 key，所有人就都能用它调用 /v1。</p>
    </div>

    <ul v-else class="community__list">
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
            <span>社区密钥 <code>ah-{{ item.id }}</code></span>
          </div>
          <div class="crow__usage">
            <div class="bar"><span class="bar__fill" :style="{ width: `${percent(item)}%` }" /></div>
            <span class="crow__count">{{ usageText(item) }}</span>
          </div>
        </div>
        <div class="crow__actions">
          <button class="icon-btn" type="button" title="复制社区密钥" @click="copy(`ah-${item.id}`)">
            <AppIcon name="copy" :size="15" />
          </button>
          <button class="icon-btn icon-btn--danger" type="button" title="删除" @click="remove(item)">
            <AppIcon name="trash" :size="15" />
          </button>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.community__head {
  flex-wrap: wrap;
  gap: 14px;
}

.community__sub {
  max-width: 68ch;
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-soft);
  line-height: 1.6;
}

.community__actions {
  display: flex;
  gap: 10px;
}

.community__issued {
  justify-content: flex-start;
  margin: 0 16px 12px;
}

.community__issued code {
  margin: 0 4px;
}

.community__form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px;
  margin: 0 16px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-inset);
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

.community__list {
  list-style: none;
  margin: 0;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.community__skeleton {
  height: 104px;
}

.community__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 24px;
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
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-inset);
  transition: border-color 0.16s ease, background 0.16s ease;
}

.crow:hover {
  border-color: var(--accent-border);
  background: var(--bg-elev);
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

.icon-btn--danger:hover:not(:disabled) {
  color: var(--danger);
}
</style>
