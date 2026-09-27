<script setup lang="ts">
import AppIcon from './AppIcon.vue'
import { demo } from '../store/demo'
</script>

<template>
  <Transition name="slide">
    <div v-if="demo.active.value" class="demo-banner" role="status">
      <AppIcon name="alert" :size="16" />
      <span>
        未连接后端服务，当前为 <strong>演示数据</strong>。启动 <code>main.py</code>
        （Flask 127.0.0.1:2685）后刷新即可看到真实数据。
      </span>
      <button type="button" class="demo-banner__close" title="关闭提示" @click="demo.dismiss()">
        <AppIcon name="close" :size="14" />
      </button>
    </div>
  </Transition>
</template>

<style scoped>
.demo-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 24px;
  background: var(--warn-bg);
  color: var(--warn);
  font-size: 13.5px;
  line-height: 1.5;
}

.demo-banner code {
  background: transparent;
  padding: 0;
  color: inherit;
  font-size: 0.92em;
}

.demo-banner strong {
  font-weight: 650;
}

.demo-banner__close {
  display: grid;
  place-items: center;
  margin-left: auto;
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.demo-banner__close:hover {
  background: rgba(0, 0, 0, 0.06);
}

.slide-enter-active,
.slide-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-100%);
}
</style>
