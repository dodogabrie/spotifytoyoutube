<script setup lang="ts">
import { onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AppCard from '../components/AppCard.vue'
import AppButton from '../components/AppButton.vue'
import PageHeader from '../components/PageHeader.vue'

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
  <section class="space-y-8">
    <PageHeader
      title="Connect both accounts"
      subtitle="Authenticate Spotify and YouTube Music to continue."
    />

    <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
      <AppCard padding="lg">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold text-lg flex items-center gap-2">
            <span class="h-2.5 w-2.5 rounded-full bg-spotify-500" />
            Spotify
          </h2>
          <span v-if="authStore.spotifyConnected" class="text-success-600 text-sm font-medium">
            Connected
          </span>
        </div>
        <p class="text-fg-secondary text-sm mt-2">Standard OAuth with PKCE — your token stays in this session.</p>
        <div class="mt-5">
          <AppButton
            tone="spotify"
            :disabled="authStore.spotifyConnected"
            @click="connectSpotify"
          >
            {{ authStore.spotifyConnected ? 'Connected' : 'Connect Spotify' }}
          </AppButton>
        </div>
      </AppCard>

      <AppCard padding="lg">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold text-lg flex items-center gap-2">
            <span class="h-2.5 w-2.5 rounded-full bg-ytmusic-500" />
            YouTube Music
          </h2>
          <span v-if="authStore.ytmusicConnected" class="text-success-600 text-sm font-medium">
            Connected
          </span>
        </div>
        <p class="text-fg-secondary text-sm mt-2">Google device-code flow — no third-party password ever entered here.</p>

        <template v-if="authStore.deviceFlow">
          <div class="mt-5 rounded-card bg-surface-muted p-4">
            <p class="text-sm">
              Open
              <a class="text-info-600 underline break-all" :href="authStore.deviceFlow.verification_url" target="_blank" rel="noopener">
                {{ authStore.deviceFlow.verification_url }}
              </a>
              and enter:
            </p>
            <div class="mt-3 text-2xl sm:text-3xl font-mono tracking-[0.4em] text-center py-3 rounded-control bg-surface border border-border">
              {{ authStore.deviceFlow.user_code }}
            </div>
            <p class="text-fg-muted text-xs mt-2 text-center">Waiting for authorization…</p>
          </div>
        </template>
        <div v-else class="mt-5">
          <AppButton
            tone="ytmusic"
            :disabled="authStore.ytmusicConnected"
            @click="startYTMusic"
          >
            {{ authStore.ytmusicConnected ? 'Connected' : 'Connect YouTube Music' }}
          </AppButton>
        </div>
      </AppCard>
    </div>

    <div
      v-if="error"
      class="rounded-card border border-danger-200 bg-danger-50 text-danger-700 text-sm px-4 py-3"
    >
      {{ error }}
    </div>

    <div class="flex flex-col sm:flex-row gap-3 sm:items-center">
      <AppButton
        :disabled="!authStore.spotifyConnected || !authStore.ytmusicConnected"
        @click="continueNext"
      >
        Continue
      </AppButton>
      <span v-if="!authStore.spotifyConnected || !authStore.ytmusicConnected" class="text-sm text-fg-muted">
        Both connections are required.
      </span>
    </div>
  </section>
</template>
