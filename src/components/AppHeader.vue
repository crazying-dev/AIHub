<script setup lang="ts">
import { ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import AppIcon from './AppIcon.vue'
import { session } from '../store/session'
import { theme } from '../store/theme'
import { toast } from '../store/toast'

const route = useRoute()
const router = useRouter()

// 顶层绑定在模板中会自动解包 ref，所以这里解构后直接当值使用
const { isAuthed, initial, profile } = session
const { current: themeMode } = theme

const navItems = [
  { name: 'home', label: '首页', to: '/' },
  { name: 'docs', label: '接入文档', to: '/docs' },
  { name: 'console', label: '控制台', to: '/console' },
] as const

const menuOpen = ref(false)

// 路由切换时收起移动端菜单
watch(() => route.fullPath, () => {
  menuOpen.value = false
})

function signOut(): void {
  session.signOut()
  toast.info('已退出登录')
  void router.push('/')
}
</script>

<template>
  <header class="header">
    <div class="header__inner">
      <RouterLink class="brand" to="/">
        <span class="brand__mark">
          <AppIcon name="spark" :size="18" :stroke="2" />
        </span>
        <span class="brand__text">AIHub</span>
        <span class="brand__tag">统一 AI 网关</span>
      </RouterLink>

      <nav class="nav" :class="{ 'nav--open': menuOpen }">
        <RouterLink
          v-for="item in navItems"
          :key="item.name"
          class="nav__link"
          active-class="nav__link--active"
          :to="item.to"
        >
          {{ item.label }}
        </RouterLink>

        <div class="nav__actions">
          <button
            v-if="isAuthed"
            type="button"
            class="btn btn--ghost btn--sm nav__user"
            title="退出登录"
            @click="signOut"
          >
            <span class="avatar">{{ initial }}</span>
            <span class="nav__user-name">{{ profile?.name }}</span>
            <AppIcon name="logout" :size="15" />
          </button>
          <template v-else>
            <RouterLink class="btn btn--ghost btn--sm" to="/login">登录</RouterLink>
            <RouterLink class="btn btn--primary btn--sm" to="/register">免费注册</RouterLink>
          </template>
        </div>
      </nav>

      <div class="header__tools">
        <button
          type="button"
          class="icon-btn"
          :title="themeMode === 'dark' ? '切换到亮色主题' : '切换到暗色主题'"
          @click="theme.toggle()"
        >
          <AppIcon :name="themeMode === 'dark' ? 'sun' : 'moon'" :size="17" />
        </button>
        <button
          type="button"
          class="icon-btn icon-btn--menu"
          :title="menuOpen ? '收起菜单' : '展开菜单'"
          @click="menuOpen = !menuOpen"
        >
          <AppIcon :name="menuOpen ? 'close' : 'menu'" :size="18" />
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 40;
  background: color-mix(in srgb, var(--bg) 82%, transparent);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}

.header__inner {
  display: flex;
  align-items: center;
  gap: 20px;
  width: 100%;
  max-width: var(--page);
  height: var(--header-h);
  margin: 0 auto;
  padding: 0 24px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-h);
  font-weight: 650;
  font-size: 17px;
  letter-spacing: -0.01em;
}

.brand:hover {
  text-decoration: none;
}

.brand__mark {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: linear-gradient(135deg, var(--accent), var(--brand-2));
  color: #fff;
  box-shadow: var(--shadow-sm);
}

.brand__tag {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-soft);
  padding-left: 10px;
  border-left: 1px solid var(--border);
}

.nav {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 12px;
  flex: 1 1 auto;
}

.nav__link {
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-size: 15px;
  font-weight: 500;
  transition: color 0.16s ease, background 0.16s ease;
}

.nav__link:hover {
  color: var(--text-h);
  background: var(--bg-soft);
  text-decoration: none;
}

.nav__link--active {
  color: var(--accent);
  background: var(--accent-bg);
}

.nav__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.nav__user {
  padding-right: 8px;
}

.nav__user-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-h);
}

.avatar {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--accent-bg);
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
}

.header__tools {
  display: flex;
  align-items: center;
  gap: 6px;
}

.icon-btn {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.16s ease, background 0.16s ease, border-color 0.16s ease;
}

.icon-btn:hover {
  color: var(--text-h);
  background: var(--bg-soft);
}

.icon-btn--menu {
  display: none;
}

@media (max-width: 860px) {
  .brand__tag {
    display: none;
  }

  .icon-btn--menu {
    display: grid;
  }

  .nav {
    position: absolute;
    top: var(--header-h);
    left: 0;
    right: 0;
    display: none;
    flex-direction: column;
    align-items: stretch;
    gap: 6px;
    margin: 0;
    padding: 14px 20px 18px;
    background: var(--bg-elev);
    border-bottom: 1px solid var(--border);
    box-shadow: var(--shadow);
  }

  .nav--open {
    display: flex;
  }

  .nav__actions {
    margin: 6px 0 0;
    flex-wrap: wrap;
  }
}
</style>
