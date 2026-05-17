<script setup lang="ts">
defineProps<{ title: string; subtitle?: string }>()
</script>

<template>
  <header class="space-y-2">
    <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-fg-primary">{{ title }}</h1>
    <p v-if="subtitle" class="text-fg-secondary text-base">{{ subtitle }}</p>
  </header>
</template>
