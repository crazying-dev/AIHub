<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AppIcon from './AppIcon.vue'

defineProps<{
  title: string
  subtitle: string
  /** 卡片底部提示文案与链接 */
  footText: string
  footLinkText: string
  footLinkTo: string
}>()
</script>

<template>
  <div class="auth">
    <div class="auth__glow" aria-hidden="true" />
    <div class="auth__card card">
      <header class="auth__head">
        <span class="auth__mark"><AppIcon name="spark" :size="18" :stroke="2" /></span>
        <h1>{{ title }}</h1>
        <p>{{ subtitle }}</p>
      </header>

      <slot />

      <footer class="auth__foot">
        <span>{{ footText }}</span>
        <RouterLink :to="footLinkTo">{{ footLinkText }}</RouterLink>
      </footer>
    </div>

    <p class="auth__legal">
      继续即表示你同意服务条款与隐私政策；本项目目前为演示版本。
    </p>
  </div>
</template>

<style scoped>
.auth {
  position: relative;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 56px 24px 72px;
}

.auth__glow {
  position: absolute;
  top: -120px;
  left: 50%;
  width: 620px;
  max-width: 120vw;
  height: 420px;
  transform: translateX(-50%);
  background: radial-gradient(
    circle at 50% 50%,
    color-mix(in srgb, var(--accent) 20%, transparent),
    transparent 65%
  );
  pointer-events: none;
}

.auth__card {
  position: relative;
  width: 100%;
  max-width: 440px;
  padding: 32px;
  box-shadow: var(--shadow-lg);
}

.auth__head {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
  margin-bottom: 24px;
}

.auth__mark {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  margin-bottom: 4px;
  border-radius: 11px;
  background: linear-gradient(135deg, var(--accent), var(--brand-2));
  color: #fff;
}

.auth__head h1 {
  font-size: 26px;
}

.auth__head p {
  font-size: 14.5px;
}

.auth__foot {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid var(--border);
  font-size: 14px;
  color: var(--text-muted);
}

.auth__legal {
  font-size: 12.5px;
  color: var(--text-soft);
  text-align: center;
  max-width: 420px;
}
</style>
