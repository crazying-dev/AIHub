<script setup lang="ts">
import { ref } from 'vue'
import AppIcon from './AppIcon.vue'

const props = withDefaults(
  defineProps<{ code: string; label?: string; language?: string }>(),
  { label: '', language: '' },
)

const copied = ref(false)
let timer: number | undefined

async function copy(): Promise<void> {
  try {
    await navigator.clipboard.writeText(props.code)
  } catch {
    // 非安全上下文（如 http 局域网访问）下 clipboard 不可用，降级为选中文本
    const area = document.createElement('textarea')
    area.value = props.code
    document.body.appendChild(area)
    area.select()
    document.execCommand('copy')
    area.remove()
  }
  copied.value = true
  window.clearTimeout(timer)
  timer = window.setTimeout(() => {
    copied.value = false
  }, 1600)
}
</script>

<template>
  <div class="code">
    <div class="code__bar">
      <span class="code__label">{{ label || language || 'code' }}</span>
      <button type="button" class="code__copy" :title="copied ? '已复制' : '复制代码'" @click="copy">
        <AppIcon :name="copied ? 'check' : 'copy'" :size="14" />
        {{ copied ? '已复制' : '复制' }}
      </button>
    </div>
    <pre class="code-block"><code>{{ code }}</code></pre>
  </div>
</template>

<style scoped>
.code {
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--code-border);
  background: var(--code-bg);
}

.code__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px 8px 14px;
  border-bottom: 1px solid var(--code-border);
  color: rgba(232, 230, 242, 0.72);
  font-family: var(--mono);
  font-size: 12px;
}

.code__copy {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 9px;
  border: 1px solid transparent;
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.06);
  color: inherit;
  font-family: var(--sans);
  font-size: 12px;
  cursor: pointer;
  transition: background 0.16s ease, color 0.16s ease;
}

.code__copy:hover {
  background: rgba(255, 255, 255, 0.14);
  color: #fff;
}

.code :deep(pre.code-block) {
  border: none;
  border-radius: 0;
}
</style>
