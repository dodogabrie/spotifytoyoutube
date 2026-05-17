<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useTransferStore } from '../stores/transfer'
import AppCard from '../components/AppCard.vue'
import PageHeader from '../components/PageHeader.vue'

const router = useRouter()
const store = useTransferStore()

function choose(dir: 'spotify_to_ytmusic' | 'ytmusic_to_spotify') {
  store.direction = dir
  router.push('/login')
}
</script>

<template>
  <section class="space-y-8 sm:space-y-10">
    <PageHeader
      title="Transfer your playlists"
      subtitle="Pick a direction to begin. Your personal playlists, copied across with one click."
    />

    <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
      <AppCard variant="interactive" padding="lg" @click="choose('spotify_to_ytmusic')">
        <div class="flex flex-col gap-3">
          <div class="flex items-center gap-2 text-xs uppercase tracking-wider text-fg-secondary">
            <span class="h-2 w-2 rounded-full bg-spotify-500" />
            Direction
          </div>
          <div class="text-xl sm:text-2xl font-semibold">
            Spotify <span class="text-fg-muted">→</span> YouTube Music
          </div>
          <p class="text-fg-secondary">
            Copy your personal Spotify playlists into YouTube Music.
            ISRC-aware matching, duplicate-safe by default.
          </p>
        </div>
      </AppCard>

      <AppCard variant="interactive" padding="lg" @click="choose('ytmusic_to_spotify')">
        <div class="flex flex-col gap-3">
          <div class="flex items-center gap-2 text-xs uppercase tracking-wider text-fg-secondary">
            <span class="h-2 w-2 rounded-full bg-ytmusic-500" />
            Direction
          </div>
          <div class="text-xl sm:text-2xl font-semibold">
            YouTube Music <span class="text-fg-muted">→</span> Spotify
          </div>
          <p class="text-fg-secondary">
            Copy your YouTube Music library playlists into Spotify.
            Same matching engine, same idempotency choices.
          </p>
        </div>
      </AppCard>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
      <div class="rounded-card border border-border bg-surface p-4">
        <div class="font-medium">Match-aware</div>
        <p class="text-fg-secondary mt-1">RapidFuzz-scored search with ISRC bonus, configurable threshold.</p>
      </div>
      <div class="rounded-card border border-border bg-surface p-4">
        <div class="font-medium">Idempotent</div>
        <p class="text-fg-secondary mt-1">Create new, append, replace or skip when a playlist already exists.</p>
      </div>
      <div class="rounded-card border border-border bg-surface p-4">
        <div class="font-medium">Privacy-first</div>
        <p class="text-fg-secondary mt-1">Tokens stay in your session — never written to disk in the web flow.</p>
      </div>
    </div>
  </section>
</template>
