import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import { session } from '../store/session'

/** 页面路由表（少量页面 + 404） */
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { title: '首页' },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
    meta: { title: '注册' },
  },
  {
    path: '/console',
    name: 'console',
    component: () => import('../views/ConsoleView.vue'),
    meta: { title: '控制台', requiresAuth: true },
  },
  {
    path: '/docs',
    name: 'docs',
    component: () => import('../views/DocsView.vue'),
    meta: { title: '接入文档' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFoundView.vue'),
    meta: { title: '页面不存在' },
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    return savedPosition ?? { top: 0 }
  },
})

router.beforeEach((to) => {
  // 未登录访问控制台 -> 去登录页，并记住来路
  if (to.meta.requiresAuth && !session.isAuthed.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  // 已登录不再展示登录/注册页
  if (session.isAuthed.value && (to.name === 'login' || to.name === 'register')) {
    return { name: 'console' }
  }
  return true
})

router.afterEach((to) => {
  const title = typeof to.meta.title === 'string' ? to.meta.title : ''
  document.title = title ? `${title} · AIHub` : 'AIHub'
})
