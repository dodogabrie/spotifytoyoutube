<script setup lang="ts">
type Tone = 'success' | 'warning' | 'muted'
const props = withDefaults(defineProps<{ label: string; value: number | string; tone?: Tone }>(), {
  tone: 'muted',
})

const valueClass = {
  success: 'text-success-600',
  warning: 'text-warning-600',
  muted: 'text-fg-primary',
}[props.tone]
</script>

<template>
  <div class="rounded-card border border-border bg-surface shadow-card p-4 sm:p-5">
    <div class="text-xs text-fg-secondary uppercase tracking-wider">{{ label }}</div>
    <div :class="['text-3xl sm:text-4xl font-bold mt-2 tabular-nums', valueClass]">{{ value }}</div>
  </div>
</template>
