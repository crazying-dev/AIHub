<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AppIcon from './AppIcon.vue'

const year = new Date().getFullYear()
</script>

<template>
  <footer class="footer">
    <div class="footer__inner">
      <div class="footer__about">
        <div class="footer__brand">
          <span class="footer__mark"><AppIcon name="spark" :size="16" :stroke="2" /></span>
          AIHub
        </div>
        <p>一个密钥，接入全部主流大模型。OpenAI 兼容协议，改一行 base_url 即可迁移。</p>
      </div>

      <nav class="footer__cols">
        <div class="footer__col">
          <h4>产品</h4>
          <RouterLink to="/docs">接入文档</RouterLink>
          <RouterLink to="/console">控制台</RouterLink>
          <RouterLink to="/register">免费注册</RouterLink>
        </div>
        <div class="footer__col">
          <h4>开发者</h4>
          <RouterLink to="/docs">快速开始</RouterLink>
          <RouterLink to="/docs">API 参考</RouterLink>
          <a href="/v1/chat/completions">接口地址</a>
        </div>
        <div class="footer__col">
          <h4>关于</h4>
          <a href="https://github.com/crazying-dev" target="_blank" rel="noreferrer">GitHub</a>
          <a href="mailto:ourpet001@163.com">联系我们</a>
        </div>
      </nav>
    </div>

    <div class="footer__bar">
      <span>© {{ year }} AIHub · ComputeRelay</span>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  border-top: 1px solid var(--border);
  background: var(--bg-elev);
}

.footer__inner {
  display: flex;
  flex-wrap: wrap;
  gap: 40px;
  justify-content: space-between;
  width: 100%;
  max-width: var(--page);
  margin: 0 auto;
  padding: 44px 24px 32px;
}

.footer__about {
  max-width: 320px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.footer__brand {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-h);
  font-weight: 650;
}

.footer__mark {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--accent), var(--brand-2));
  color: #fff;
}

.footer__about p {
  font-size: 14px;
}

.footer__cols {
  display: flex;
  gap: 64px;
}

.footer__col {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.footer__col h4 {
  margin-bottom: 4px;
  font-size: 13px;
  color: var(--text-h);
  letter-spacing: 0.04em;
}

.footer__col a {
  color: var(--text-muted);
  font-size: 14px;
}

.footer__col a:hover {
  color: var(--accent);
}

.footer__bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: space-between;
  width: 100%;
  max-width: var(--page);
  margin: 0 auto;
  padding: 16px 24px 26px;
  border-top: 1px solid var(--border);
  color: var(--text-soft);
  font-size: 13px;
}

@media (max-width: 720px) {
  .footer__cols {
    gap: 32px;
    flex-wrap: wrap;
  }
}
</style>
