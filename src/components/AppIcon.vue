<script setup lang="ts">
import { computed } from 'vue'

/**
 * 极简线性图标集（不引入图标库，避免额外依赖）。
 * 全部描边式 24x24，颜色继承 currentColor。
 */
const icons: Record<string, string[]> = {
  spark: ['M12 2l1.9 5.2L19 9.1l-5.1 1.9L12 16.2l-1.9-5.2L5 9.1l5.1-1.9L12 2z'],
  bolt: ['M13 2 3 14h9l-1 8 10-12h-9l1-8z'],
  shield: ['M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z', 'm9 12 2 2 4-4'],
  chart: ['M3 3v18h18', 'M7 16v-5', 'M12 16V8', 'M17 16v-8'],
  layers: ['m12 2 9 5-9 5-9-5 9-5z', 'm3 12 9 5 9-5', 'm3 17 9 5 9-5'],
  copy: [
    'M9 9h10a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2V11a2 2 0 0 1 2-2z',
    'M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1',
  ],
  check: ['M20 6 9 17l-5-5'],
  plus: ['M5 12h14', 'M12 5v14'],
  eye: ['M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7z', 'M12 12a3 3 0 1 0 0-6 3 3 0 0 0 0 6z'],
  'eye-off': ['m2 2 20 20', 'M6.8 6.9C4.1 8.5 2 12 2 12s3.6 7 10 7c1.9 0 3.5-.6 4.9-1.4', 'M12 17a5 5 0 0 0 4.6-7'],
  sun: ['M12 16.5a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9z', 'M12 2v2', 'M12 20v2', 'M2 12h2', 'M20 12h2', 'm5 5 1.5 1.5', 'm17.5 17.5 1.5 1.5', 'm19 5-1.5 1.5', 'm6.5 17.5-1.5 1.5'],
  moon: ['M21 13A9 9 0 1 1 11 3a7 7 0 0 0 10 10z'],
  'arrow-right': ['M5 12h14', 'm12 5 7 7-7 7'],
  lock: ['M7 11V7a5 5 0 0 1 10 0v4', 'M5 11h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2z'],
  book: ['M4 19.5A2.5 2.5 0 0 1 6.5 17H20', 'M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z'],
  menu: ['M4 6h16', 'M4 12h16', 'M4 18h16'],
  close: ['M18 6 6 18', 'm6 6 12 12'],
  clock: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z', 'M12 7v5l3 2'],
  globe: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z', 'M3 12h18', 'M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18z'],
  code: ['m16 18 6-6-6-6', 'm8 6-6 6 6 6'],
  user: ['M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z', 'M4 21a8 8 0 0 1 16 0'],
  logout: ['M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4', 'm16 17 5-5-5-5', 'M21 12H9'],
  trash: ['M3 6h18', 'M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2', 'M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6'],
  'alert': ['M12 9v4', 'M12 17h.01', 'M12 3 2 20h20L12 3z'],
  dot: ['M12 12h.01'],
}

const props = withDefaults(defineProps<{ name: string; size?: number; stroke?: number }>(), {
  size: 18,
  stroke: 1.7,
})

const paths = computed(() => icons[props.name] ?? icons.dot)
</script>

<template>
  <svg
    class="icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="stroke"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path v-for="(d, index) in paths" :key="index" :d="d" />
  </svg>
</template>

<style scoped>
.icon {
  flex: none;
  display: block;
}
</style>
