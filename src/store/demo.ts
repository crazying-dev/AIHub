import { computed, ref } from 'vue'

/**
 * 演示模式开关。
 *
 * 当后端（Flask: 127.0.0.1:2685）未启动、数据库不可用时，
 * api/client.ts 会捕获网络错误并打开此开关，页面改用本地演示数据渲染，
 * 保证纯前端也能完整走一遍交互。（用户说“不用管核心业务未完成”）
 */
const active = ref(false)
const activatedAt = ref<number | null>(null)

const STORAGE_KEY = 'aihub.demo-dismissed'

const dismissed = ref(readDismissed())

function readDismissed(): boolean {
  try {
    return window.sessionStorage.getItem(STORAGE_KEY) === '1'
  } catch {
    return false
  }
}

export const demo = {
  active: computed(() => active.value && !dismissed.value),
  activatedAt: computed(() => activatedAt.value),
  activate(): void {
    if (active.value) return
    active.value = true
    activatedAt.value = Date.now()
  },
  /** 用户手动关闭提示条（本次会话内不再显示） */
  dismiss(): void {
    dismissed.value = true
    try {
      window.sessionStorage.setItem(STORAGE_KEY, '1')
    } catch {
      /* ignore */
    }
  },
}
