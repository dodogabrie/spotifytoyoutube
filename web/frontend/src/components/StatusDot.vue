<script setup lang="ts">
const props = defineProps<{ connected: boolean; label: string }>()
</script>

<template>
  <span class="inline-flex items-center gap-1.5 text-sm">
    <span
      :class="[
        'h-2 w-2 rounded-full',
        connected ? 'bg-success-500 shadow-[0_0_0_4px_rgba(16,185,129,0.15)]' : 'bg-fg-muted',
      ]"
    />
    <span :class="connected ? 'text-fg-primary' : 'text-fg-muted'">{{ label }}</span>
  </span>
</template>
