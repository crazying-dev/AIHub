import { readonly, ref } from 'vue'

export type ToastKind = 'ok' | 'error' | 'info'

export interface ToastItem {
  id: number
  kind: ToastKind
  text: string
}

const items = ref<ToastItem[]>([])
let seq = 0

export const toasts = readonly(items)

function dismiss(id: number): void {
  items.value = items.value.filter((item) => item.id !== id)
}

function push(text: string, kind: ToastKind = 'info', duration = 3200): void {
  const id = ++seq
  items.value = [...items.value, { id, kind, text }]
  if (duration > 0) {
    window.setTimeout(() => dismiss(id), duration)
  }
}

export const toast = {
  ok: (text: string) => push(text, 'ok'),
  error: (text: string) => push(text, 'error'),
  info: (text: string) => push(text, 'info'),
  dismiss,
}
