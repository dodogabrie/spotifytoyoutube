<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
onMounted(() => authStore.refresh())
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <header class="bg-white border-b border-slate-200">
      <div class="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
        <RouterLink to="/" class="text-lg font-semibold">Spotify ⇄ YouTube Music</RouterLink>
        <nav class="text-sm text-slate-500 flex gap-4">
          <span :class="authStore.spotifyConnected ? 'text-green-600' : 'text-slate-400'">
            ● Spotify
          </span>
          <span :class="authStore.ytmusicConnected ? 'text-green-600' : 'text-slate-400'">
            ● YT Music
          </span>
        </nav>
      </div>
    </header>
    <main class="flex-1">
      <div class="max-w-5xl mx-auto px-6 py-8">
        <RouterView />
      </div>
    </main>
  </div>
</template>
