<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { useAuthStore } from './stores/auth'
import StatusDot from './components/StatusDot.vue'

const authStore = useAuthStore()
onMounted(() => authStore.refresh())
</script>

<template>
  <div class="min-h-screen flex flex-col bg-page text-fg-primary">
    <header class="sticky top-0 z-10 bg-surface/80 backdrop-blur border-b border-border">
      <div class="max-w-shell mx-auto px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between gap-3">
        <RouterLink to="/" class="flex items-center gap-2 font-semibold tracking-tight text-base sm:text-lg">
          <span class="inline-block h-6 w-6 rounded-md bg-gradient-to-br from-spotify-500 to-ytmusic-500" />
          <span class="hidden sm:inline">Spotify ⇄ YouTube Music</span>
          <span class="sm:hidden">Sp ⇄ YTM</span>
        </RouterLink>
        <nav class="flex gap-4">
          <StatusDot :connected="authStore.spotifyConnected" label="Spotify" />
          <StatusDot :connected="authStore.ytmusicConnected" label="YT Music" />
        </nav>
      </div>
    </header>
    <main class="flex-1">
      <div class="max-w-shell mx-auto px-4 sm:px-6 py-6 sm:py-10">
        <RouterView />
      </div>
    </main>
    <footer class="border-t border-border py-4">
      <div class="max-w-shell mx-auto px-4 sm:px-6 text-xs text-fg-muted text-center">
        Open source · Spotify & YouTube Music playlist transfer
      </div>
    </footer>
  </div>
</template>
