<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { transfer as transferApi } from '../api/transfer'
import AppCard from '../components/AppCard.vue'
import PageHeader from '../components/PageHeader.vue'
import ProgressBar from '../components/ProgressBar.vue'

const props = defineProps<{ jobId: string }>()
const router = useRouter()

const events = ref<Array<Record<string, any>>>([])
const status = ref<'connecting' | 'streaming' | 'closed'>('connecting')
const overall = ref({ current: 0, total: 0 })
const playlist = ref({ name: '', current: 0, total: 0 })
const finalStatus = ref<'queued' | 'running' | 'done' | 'error'>('running')
let ws: WebSocket | null = null

function handle(evt: Record<string, any>) {
  if (evt.type === 'ping' || evt.type === 'stream_closed') return
  events.value.push(evt)
  if (evt.type === 'job_started') {
    overall.value = { current: 0, total: evt.total ?? 0 }
  } else if (evt.type === 'playlist_started') {
    playlist.value = { name: evt.playlist_name ?? '', current: 0, total: evt.total ?? 0 }
  } else if (evt.type === 'track_matched' || evt.type === 'track_unmatched') {
    playlist.value = {
      name: playlist.value.name,
      current: evt.current ?? playlist.value.current,
      total: evt.total ?? playlist.value.total,
    }
  } else if (evt.type === 'playlist_done') {
    overall.value.current += 1
  } else if (evt.type === 'job_done') {
    finalStatus.value = 'done'
    setTimeout(() => router.push(`/done/${props.jobId}`), 500)
  } else if (evt.type === 'error') {
    finalStatus.value = 'error'
  }
}

function connect() {
  ws = new WebSocket(transferApi.streamUrl(props.jobId))
  ws.onopen = () => (status.value = 'streaming')
  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data)
      if (data.type === 'stream_closed') {
        status.value = 'closed'
        if (data.status === 'done') router.push(`/done/${props.jobId}`)
        return
      }
      handle(data)
    } catch {
      // ignore malformed
    }
  }
  ws.onerror = () => (status.value = 'closed')
  ws.onclose = () => (status.value = 'closed')
}

onMounted(connect)
onBeforeUnmount(() => ws?.close())

const statusTone = {
  connecting: 'bg-warning-500',
  streaming: 'bg-success-500 animate-pulse',
  closed: 'bg-fg-muted',
} as const

const eventTones: Record<string, string> = {
  track_matched: 'text-success-700',
  track_unmatched: 'text-warning-700',
  playlist_started: 'text-info-700',
  playlist_done: 'text-info-700',
  job_started: 'text-info-700',
  job_done: 'text-success-700',
  error: 'text-danger-700',
}
</script>

<template>
  <section class="space-y-6 sm:space-y-8">
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
      <PageHeader title="Transferring…" :subtitle="`Job ${jobId}`" />
      <div class="flex items-center gap-2 text-sm">
        <span :class="['h-2 w-2 rounded-full', statusTone[status]]" />
        <span class="text-fg-secondary capitalize">{{ status }}</span>
      </div>
    </div>

    <AppCard padding="md">
      <div class="space-y-5">
        <ProgressBar
          label="Overall"
          :current="overall.current"
          :total="overall.total"
          tone="spotify"
        />
        <ProgressBar
          v-if="playlist.name"
          :label="playlist.name"
          :current="playlist.current"
          :total="playlist.total"
          tone="info"
        />
      </div>
    </AppCard>

    <AppCard padding="sm">
      <div class="px-1 sm:px-2 py-2 text-xs uppercase tracking-wider text-fg-secondary border-b border-divider">
        Live log
      </div>
      <ul class="max-h-[28rem] overflow-y-auto text-sm font-mono">
        <li
          v-for="(e, i) in events.slice(-300)"
          :key="i"
          class="px-1 sm:px-2 py-1.5 border-b last:border-0 border-divider/60"
        >
          <span :class="['inline-block min-w-[140px]', eventTones[e.type] ?? 'text-fg-secondary']">
            [{{ e.type }}]
          </span>
          <span class="text-fg-primary">
            {{ e.playlist_name ? `${e.playlist_name} — ` : '' }}{{ e.track_title ?? e.message ?? '' }}
          </span>
        </li>
        <li v-if="events.length === 0" class="text-fg-muted text-center py-10">Waiting for events…</li>
      </ul>
    </AppCard>
  </section>
</template>
