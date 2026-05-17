import { defineStore } from 'pinia'
import { ref } from 'vue'
import { auth, type YTMusicStart } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const spotifyConnected = ref(false)
  const ytmusicConnected = ref(false)
  const deviceFlow = ref<YTMusicStart | null>(null)
  const polling = ref(false)

  async function refresh() {
    try {
      const s = await auth.status()
      spotifyConnected.value = s.spotify_connected
      ytmusicConnected.value = s.ytmusic_connected
    } catch {
      spotifyConnected.value = false
      ytmusicConnected.value = false
    }
  }

  async function startYTMusicFlow() {
    deviceFlow.value = await auth.ytmusicStart()
    polling.value = true
  }

  async function pollYTMusic(): Promise<'pending' | 'authorized' | 'expired' | 'denied' | 'error'> {
    if (!deviceFlow.value) return 'error'
    const r = await auth.ytmusicPoll()
    if (r.status === 'authorized') {
      ytmusicConnected.value = true
      polling.value = false
      deviceFlow.value = null
    } else if (r.status === 'expired' || r.status === 'denied' || r.status === 'error') {
      polling.value = false
      deviceFlow.value = null
    }
    return r.status
  }

  return { spotifyConnected, ytmusicConnected, deviceFlow, polling, refresh, startYTMusicFlow, pollYTMusic }
})
