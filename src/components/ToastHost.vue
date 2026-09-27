<script setup lang="ts">
import AppIcon from './AppIcon.vue'
import { toast, toasts } from '../store/toast'

const icons = { ok: 'check', error: 'alert', info: 'spark' } as const
</script>

<template>
  <div class="toast-host" aria-live="polite">
    <TransitionGroup name="toast">
      <div v-for="item in toasts" :key="item.id" class="toast" :class="`toast--${item.kind}`">
        <AppIcon :name="icons[item.kind]" :size="16" />
        <span>{{ item.text }}</span>
        <button
          type="button"
          class="toast__close"
          title="关闭"
          @click="toast.dismiss(item.id)"
        >
          <AppIcon name="close" :size="13" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-host {
  position: fixed;
  top: 18px;
  right: 18px;
  z-index: 90;
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: min(360px, calc(100vw - 36px));
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-elev);
  color: var(--text-h);
  font-size: 14px;
  box-shadow: var(--shadow-lg);
}

.toast--ok {
  color: var(--ok);
  border-color: var(--ok-bg);
}

.toast--error {
  color: var(--danger);
  border-color: var(--danger-bg);
}

.toast--info {
  color: var(--text-h);
}

.toast__close {
  display: grid;
  place-items: center;
  margin-left: auto;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-soft);
  cursor: pointer;
}

.toast__close:hover {
  background: var(--bg-soft);
  color: var(--text-h);
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
