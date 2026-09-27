import { computed, ref } from 'vue'

/**
 * 登录态。
 *
 * 注意：后端 /api/sign 下发的是 HttpOnly Cookie（token / id），前端 JS 读不到，
 * 所以这里只在本地保存一份「展示用」的用户资料，用于导航栏与页面渲染；
 * 真正的鉴权仍由浏览器携带 Cookie 交给后端校验（见 api/client.ts）。
 */
export interface Profile {
  name: string
  email: string
  id?: string
}

const STORAGE_KEY = 'aihub.profile'

function readStorage(): Profile | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<Profile>
    if (!parsed || typeof parsed.email !== 'string') return null
    return { name: typeof parsed.name === 'string' ? parsed.name : parsed.email, email: parsed.email, id: parsed.id }
  } catch {
    return null
  }
}

const profile = ref<Profile | null>(readStorage())

function persist(): void {
  try {
    if (profile.value) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(profile.value))
    } else {
      window.localStorage.removeItem(STORAGE_KEY)
    }
  } catch {
    /* 隐私模式下 localStorage 不可用，忽略 */
  }
}

export const session = {
  profile: computed(() => profile.value),
  isAuthed: computed(() => profile.value !== null),
  /** 取用户名的首字母用于头像占位 */
  initial: computed(() => {
    const name = profile.value?.name ?? profile.value?.email ?? '?'
    return name.trim().charAt(0).toUpperCase() || '?'
  }),
  signIn(next: Profile): void {
    profile.value = next
    persist()
  },
  signOut(): void {
    profile.value = null
    persist()
  },
}
