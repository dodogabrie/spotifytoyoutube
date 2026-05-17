<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useTransferStore } from '../stores/transfer'

const router = useRouter()
const store = useTransferStore()

function choose(dir: 'spotify_to_ytmusic' | 'ytmusic_to_spotify') {
  store.direction = dir
  router.push('/login')
}
</script>

<template>
  <section class="space-y-8">
    <header>
      <h1 class="text-3xl font-bold">Transfer your playlists</h1>
      <p class="text-slate-500 mt-2">Pick a direction to begin.</p>
    </header>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <button
        class="rounded-xl border border-slate-200 bg-white p-8 text-left hover:border-emerald-500 hover:shadow"
        @click="choose('spotify_to_ytmusic')"
      >
        <div class="text-sm uppercase tracking-wide text-slate-400">Direction</div>
        <div class="text-xl font-semibold mt-1">Spotify → YouTube Music</div>
        <p class="mt-3 text-slate-500">
          Copy your personal Spotify playlists into YouTube Music.
        </p>
      </button>
      <button
        class="rounded-xl border border-slate-200 bg-white p-8 text-left hover:border-rose-500 hover:shadow"
        @click="choose('ytmusic_to_spotify')"
      >
        <div class="text-sm uppercase tracking-wide text-slate-400">Direction</div>
        <div class="text-xl font-semibold mt-1">YouTube Music → Spotify</div>
        <p class="mt-3 text-slate-500">
          Copy your YouTube Music library playlists into Spotify.
        </p>
      </button>
    </div>
  </section>
</template>
