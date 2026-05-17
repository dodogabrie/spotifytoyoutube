<script setup lang="ts">
type Variant = 'default' | 'interactive'
const props = withDefaults(defineProps<{ variant?: Variant; padding?: 'sm' | 'md' | 'lg' }>(), {
  variant: 'default',
  padding: 'md',
})

const paddingClass = {
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-6 sm:p-8',
}[props.padding]
</script>

<template>
  <div
    :class="[
      'rounded-card border border-border bg-surface shadow-card transition',
      paddingClass,
      variant === 'interactive' ? 'cursor-pointer hover:shadow-card-hover hover:-translate-y-0.5' : '',
    ]"
  >
    <slot />
  </div>
</template>
