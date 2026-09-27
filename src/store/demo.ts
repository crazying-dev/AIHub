import { computed, ref } from 'vue'

/**
 * 后端不可用标记。
 *
 * 当后端（Flask: 127.0.0.1:2685）未启动、数据库不可用时，
 * api/client.ts 会捕获网络错误并打开此开关，页面改用本地占位数据渲染，
 * 保证纯前端也能把界面渲染完整。
 */
const active = ref(false)

export const demo = {
  active: computed(() => active.value),
  activate(): void {
    active.value = true
  },
}
