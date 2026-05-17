<script setup lang="ts">
import { onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const error = ref<string | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

function connectSpotify() {
  window.location.href = '/api/auth/spotify/login'
}

async function startYTMusic() {
  error.value = null
  try {
    await authStore.startYTMusicFlow()
    const interval = (authStore.deviceFlow?.interval ?? 5) * 1000
    pollTimer = setInterval(async () => {
      const status = await authStore.pollYTMusic()
      if (status === 'authorized') {
        clearInterval(pollTimer!)
        pollTimer = null
      } else if (status === 'expired' || status === 'denied' || status === 'error') {
        clearInterval(pollTimer!)
        pollTimer = null
        error.value = `YT Music auth ${status}`
      }
    }, interval)
  } catch (e: any) {
    error.value = e?.message ?? 'YT Music start failed'
  }
}

function continueNext() {
  router.push('/playlists')
}

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <section class="space-y-6">
    <header>
      <h1 class="text-2xl font-bold">Connect both accounts</h1>
      <p class="text-slate-500 mt-1">Authenticate Spotify and YouTube Music to continue.</p>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="rounded-xl border border-slate-200 bg-white p-6">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold">Spotify</h2>
          <span v-if="authStore.spotifyConnected" class="text-green-600 text-sm">Connected ✓</span>
        </div>
        <p class="text-slate-500 text-sm mt-2">Standard OAuth with PKCE.</p>
        <button
          class="mt-4 bg-emerald-600 text-white px-4 py-2 rounded hover:bg-emerald-700"
          :disabled="authStore.spotifyConnected"
          @click="connectSpotify"
        >
          {{ authStore.spotifyConnected ? 'Connected' : 'Connect Spotify' }}
        </button>
      </div>

      <div class="rounded-xl border border-slate-200 bg-white p-6">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold">YouTube Music</h2>
          <span v-if="authStore.ytmusicConnected" class="text-green-600 text-sm">Connected ✓</span>
        </div>
        <p class="text-slate-500 text-sm mt-2">Google device-code flow.</p>
        <template v-if="authStore.deviceFlow">
          <p class="text-sm mt-3">
            Open
            <a class="text-blue-600 underline" :href="authStore.deviceFlow.verification_url" target="_blank">
              {{ authStore.deviceFlow.verification_url }}
            </a>
            and enter:
          </p>
          <div class="mt-2 text-2xl font-mono tracking-wider">{{ authStore.deviceFlow.user_code }}</div>
          <p class="text-slate-500 text-xs mt-1">Waiting for authorization…</p>
        </template>
        <button
          v-else
          class="mt-4 bg-rose-600 text-white px-4 py-2 rounded hover:bg-rose-700"
          :disabled="authStore.ytmusicConnected"
          @click="startYTMusic"
        >
          {{ authStore.ytmusicConnected ? 'Connected' : 'Connect YouTube Music' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="text-red-600 text-sm">{{ error }}</div>

    <div>
      <button
        class="bg-slate-900 text-white px-5 py-2 rounded disabled:opacity-40"
        :disabled="!authStore.spotifyConnected || !authStore.ytmusicConnected"
        @click="continueNext"
      >
        Continue
      </button>
    </div>
  </section>
</template>
