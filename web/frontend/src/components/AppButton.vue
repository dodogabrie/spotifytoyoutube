<script setup lang="ts">
type Tone = 'primary' | 'spotify' | 'ytmusic' | 'ghost' | 'danger'
type Size = 'sm' | 'md' | 'lg'

const props = withDefaults(
  defineProps<{ tone?: Tone; size?: Size; block?: boolean; type?: 'button' | 'submit' }>(),
  { tone: 'primary', size: 'md', block: false, type: 'button' },
)

const sizeClass = {
  sm: 'px-3 py-1.5 text-sm rounded-control',
  md: 'px-5 py-2.5 text-sm rounded-control',
  lg: 'px-6 py-3 text-base rounded-control',
}[props.size]

const toneClass = {
  primary: 'bg-accent-900 text-white hover:bg-accent-800',
  spotify: 'bg-spotify-600 text-white hover:bg-spotify-700',
  ytmusic: 'bg-ytmusic-600 text-white hover:bg-ytmusic-700',
  ghost: 'bg-transparent text-fg-primary border border-border hover:bg-surface-muted',
  danger: 'bg-danger-600 text-white hover:bg-danger-700',
}[props.tone]
</script>

<template>
  <button
    :type="type"
    :class="[
      'inline-flex items-center justify-center gap-2 font-medium transition shadow-card',
      'disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none',
      'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-info-500',
      sizeClass,
      toneClass,
      block ? 'w-full' : '',
    ]"
  >
    <slot />
  </button>
</template>
