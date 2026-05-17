<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    label: string
    current: number
    total: number
    tone?: 'spotify' | 'info' | 'accent'
  }>(),
  { tone: 'spotify' },
)

const pct = computed(() => (props.total ? Math.min(100, Math.round((props.current / props.total) * 100)) : 0))

const fillClass = {
  spotify: 'bg-spotify-500',
  info: 'bg-info-500',
  accent: 'bg-accent-900',
}[props.tone]
</script>

<template>
  <div>
    <div class="flex justify-between text-sm">
      <span class="text-fg-secondary">{{ label }}</span>
      <span class="text-fg-secondary tabular-nums">{{ current }}/{{ total }} · {{ pct }}%</span>
    </div>
    <div class="h-2 rounded-full bg-surface-muted mt-2 overflow-hidden">
      <div :class="['h-full rounded-full transition-all duration-500', fillClass]" :style="{ width: pct + '%' }" />
    </div>
  </div>
</template>
