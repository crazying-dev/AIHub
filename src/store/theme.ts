import { ref } from 'vue'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'aihub.theme'

function readStored(): Theme | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    return raw === 'light' || raw === 'dark' ? raw : null
  } catch {
    return null
  }
}

function systemTheme(): Theme {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

const current = ref<Theme>(readStored() ?? systemTheme())

function apply(): void {
  document.documentElement.dataset.theme = current.value
}

apply()

export const theme = {
  current,
  toggle(): void {
    current.value = current.value === 'dark' ? 'light' : 'dark'
    apply()
    try {
      window.localStorage.setItem(STORAGE_KEY, current.value)
    } catch {
      /* ignore */
    }
  },
}
