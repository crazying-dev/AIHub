<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppIcon from '../components/AppIcon.vue'
import CodeBlock from '../components/CodeBlock.vue'
import { chatSnippets } from '../data/snippets'
import { demoModels } from '../api/mock'
import { session } from '../store/session'

const { isAuthed } = session

const activeSnippet = ref(0)

const features = [
  {
    icon: 'globe',
    title: '统一 OpenAI 协议',
    desc: '一套 /v1/chat/completions 接口打穿全部模型，已有 OpenAI SDK 只需改 base_url。',
  },
  {
    icon: 'layers',
    title: '多模型自由切换',
    desc: '同一密钥调用 GPT、Claude、DeepSeek、Qwen 等模型，按需切换不换代码。',
  },
  {
    icon: 'shield',
    title: '密钥隔离与限额',
    desc: '每个项目独立密钥，支持停用与限流，泄露可一键吊销，不影响其他业务。',
  },
  {
    icon: 'chart',
    title: '用量可观测',
    desc: '请求量、Token 消耗与延迟一目了然，超预算前就能发现异常调用。',
  },
]

const highlights = [
  { label: '接入模型', value: '12+' },
  { label: '日均调用', value: '1.2M' },
  { label: '平均延迟', value: '428ms' },
  { label: '可用性', value: '99.9%' },
]
</script>

<template>
  <div class="home">
    <section class="hero">
      <div class="hero__glow" aria-hidden="true" />
      <div class="hero__inner">
        <span class="badge badge--accent hero__badge">
          <AppIcon name="bolt" :size="13" />
          OpenAI 兼容 · 一个密钥接入全部大模型
        </span>
        <h1>
          写给开发者的<br />
          <span class="hero__accent">统一 AI 接入网关</span>
        </h1>
        <p class="hero__lead">
          AIHub 把不同厂商的大模型收敛到一套标准接口下。注册、创建密钥、替换 base_url，
          三步之后代码里就只剩下一种协议。
        </p>
        <div class="hero__cta">
          <RouterLink v-if="!isAuthed" class="btn btn--primary" to="/register">
            免费开始使用
            <AppIcon name="arrow-right" :size="16" />
          </RouterLink>
          <RouterLink v-else class="btn btn--primary" to="/console">
            进入控制台
            <AppIcon name="arrow-right" :size="16" />
          </RouterLink>
          <RouterLink class="btn" to="/docs">
            <AppIcon name="book" :size="16" />
            阅读接入文档
          </RouterLink>
        </div>

        <dl class="hero__stats">
          <div v-for="item in highlights" :key="item.label" class="hero__stat">
            <dt>{{ item.label }}</dt>
            <dd>{{ item.value }}</dd>
          </div>
        </dl>
      </div>
    </section>

    <section class="page section">
      <header class="section__head">
        <span class="eyebrow">为什么选 AIHub</span>
        <h2>把模型接入这件事一次性做完</h2>
        <p>不用再为每个厂商维护一套 SDK、密钥和重试逻辑。</p>
      </header>

      <div class="features">
        <article v-for="item in features" :key="item.title" class="card feature">
          <span class="feature__icon"><AppIcon :name="item.icon" :size="18" /></span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.desc }}</p>
        </article>
      </div>
    </section>

    <section class="page section section--split">
      <div class="section__aside">
        <span class="eyebrow">支持的模型</span>
        <h2>一个密钥，跨厂商调用</h2>
        <p>
          模型列表持续更新。调用时只需修改请求体里的 <code>model</code> 字段，
          其余参数与 OpenAI 完全一致。
        </p>
        <div class="chips">
          <span v-for="model in demoModels" :key="model" class="chip mono">{{ model }}</span>
        </div>
        <RouterLink class="link" to="/docs">查看完整模型列表与限流说明
          <AppIcon name="arrow-right" :size="14" />
        </RouterLink>
      </div>

      <div class="section__code">
        <div class="tabs">
          <button
            v-for="(snippet, index) in chatSnippets"
            :key="snippet.label"
            type="button"
            class="tabs__tab"
            :class="{ 'tabs__tab--active': index === activeSnippet }"
            @click="activeSnippet = index"
          >
            {{ snippet.label }}
          </button>
        </div>
        <CodeBlock
          :code="chatSnippets[activeSnippet].code"
          :label="chatSnippets[activeSnippet].label"
        />
      </div>
    </section>

    <section class="page">
      <div class="cta">
        <div>
          <h2>现在就拿到属于你的第一个密钥</h2>
          <p>注册即可创建密钥并调用全部模型。</p>
        </div>
        <div class="cta__actions">
          <RouterLink class="btn btn--primary" to="/register">免费注册</RouterLink>
          <RouterLink class="btn" to="/login">已有账号，直接登录</RouterLink>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
}

/* Hero */
.hero {
  position: relative;
  overflow: hidden;
  border-bottom: 1px solid var(--border);
  background: var(--bg-elev);
}

.hero__glow {
  position: absolute;
  inset: -40% 20% auto;
  height: 520px;
  background: radial-gradient(
    circle at 50% 50%,
    color-mix(in srgb, var(--accent) 22%, transparent),
    transparent 62%
  );
  filter: blur(8px);
  pointer-events: none;
}

.hero__inner {
  position: relative;
  width: 100%;
  max-width: var(--page);
  margin: 0 auto;
  padding: 72px 24px 56px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 22px;
}

.hero__badge {
  background: color-mix(in srgb, var(--accent-bg) 70%, var(--bg-elev));
}

.hero h1 {
  max-width: 18ch;
}

.hero__accent {
  background: linear-gradient(120deg, var(--accent), var(--brand-2));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero__lead {
  max-width: 60ch;
  font-size: 17px;
  line-height: 1.7;
}

.hero__cta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 4px;
}

.hero__stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  width: 100%;
  margin: 26px 0 0;
  padding: 18px 0 0;
  border-top: 1px dashed var(--border);
}

.hero__stat dt {
  font-size: 13px;
  color: var(--text-soft);
}

.hero__stat dd {
  margin: 2px 0 0;
  font-size: 22px;
  font-weight: 650;
  color: var(--text-h);
  font-variant-numeric: tabular-nums;
}

/* 通用 section */
.section {
  padding-top: 64px;
  padding-bottom: 48px;
}

.section__head {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 28px;
  align-items: flex-start;
}

.section__head p {
  max-width: 58ch;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.feature {
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.feature:hover {
  transform: translateY(-3px);
  border-color: var(--accent-border);
  box-shadow: var(--shadow);
}

.feature__icon {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: var(--accent-bg);
  color: var(--accent);
}

.feature p {
  font-size: 14.5px;
  line-height: 1.65;
}

/* 模型 + 代码 */
.section--split {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr);
  gap: 40px;
  align-items: center;
}

.section__aside {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-start;
}

.section__aside p {
  line-height: 1.7;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 6px 0 4px;
}

.chip {
  padding: 5px 11px;
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  background: var(--bg-elev);
  color: var(--text-muted);
  font-size: 13px;
}

.link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14.5px;
  font-weight: 500;
}

.section__code {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.tabs {
  display: flex;
  gap: 6px;
}

.tabs__tab {
  padding: 6px 13px;
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  background: var(--bg-elev);
  color: var(--text-muted);
  font: 500 13.5px/1.4 var(--sans);
  cursor: pointer;
  transition: color 0.16s ease, background 0.16s ease, border-color 0.16s ease;
}

.tabs__tab:hover {
  color: var(--text-h);
}

.tabs__tab--active {
  color: var(--accent);
  background: var(--accent-bg);
  border-color: var(--accent-border);
}

/* CTA */
.cta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 22px;
  padding: 30px 32px;
  border: 1px solid var(--accent-border);
  border-radius: var(--radius-lg);
  background: linear-gradient(
    120deg,
    var(--accent-bg),
    color-mix(in srgb, var(--brand-2) 8%, transparent)
  );
}

.cta h2 {
  margin-bottom: 6px;
}

.cta__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

@media (max-width: 900px) {
  .section--split {
    grid-template-columns: 1fr;
    gap: 26px;
  }
}

@media (max-width: 720px) {
  .hero__inner {
    padding: 48px 16px 40px;
  }

  .hero__stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px;
  }
}
</style>
