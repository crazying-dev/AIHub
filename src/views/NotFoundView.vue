<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
</script>

<template>
  <div class="page not-found">
    <span class="not-found__code mono">404</span>
    <h1>这个页面不存在</h1>
    <p>你访问的地址没有对应的路由，确认一下链接，或者回到控制台继续。</p>
    <div class="not-found__actions">
      <RouterLink class="btn btn--primary" to="/">
        返回首页
        <AppIcon name="arrow-right" :size="16" />
      </RouterLink>
      <RouterLink class="btn" to="/console">进入控制台</RouterLink>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  padding-top: 96px;
}

.not-found__code {
  font-size: 72px;
  font-weight: 700;
  letter-spacing: 0.04em;
  background: linear-gradient(120deg, var(--accent), var(--brand-2));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.not-found p {
  max-width: 46ch;
}

.not-found__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  margin-top: 10px;
}
</style>
