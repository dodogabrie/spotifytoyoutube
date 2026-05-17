<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { transfer as transferApi } from '../api/transfer'

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

const overallPct = computed(() =>
  overall.value.total ? Math.round((overall.value.current / overall.value.total) * 100) : 0
)
const playlistPct = computed(() =>
  playlist.value.total ? Math.round((playlist.value.current / playlist.value.total) * 100) : 0
)

onMounted(connect)
onBeforeUnmount(() => ws?.close())
</script>

<template>
  <section class="space-y-6">
    <header>
      <h1 class="text-2xl font-bold">Transferring…</h1>
      <p class="text-slate-500 text-sm">Job {{ jobId }} ({{ status }})</p>
    </header>

    <div class="rounded-xl border border-slate-200 bg-white p-4 space-y-4">
      <div>
        <div class="flex justify-between text-sm">
          <span>Overall</span>
          <span>{{ overall.current }}/{{ overall.total }} ({{ overallPct }}%)</span>
        </div>
        <div class="h-2 rounded bg-slate-100 mt-1 overflow-hidden">
          <div class="h-full bg-emerald-500 transition-all" :style="{ width: overallPct + '%' }" />
        </div>
      </div>
      <div v-if="playlist.name">
        <div class="flex justify-between text-sm">
          <span>{{ playlist.name }}</span>
          <span>{{ playlist.current }}/{{ playlist.total }} ({{ playlistPct }}%)</span>
        </div>
        <div class="h-2 rounded bg-slate-100 mt-1 overflow-hidden">
          <div class="h-full bg-sky-500 transition-all" :style="{ width: playlistPct + '%' }" />
        </div>
      </div>
    </div>

    <div class="rounded-xl border border-slate-200 bg-white">
      <div class="px-4 py-2 text-sm border-b border-slate-200">Live log</div>
      <ul class="max-h-80 overflow-y-auto text-sm font-mono">
        <li v-for="(e, i) in events.slice(-200)" :key="i" class="px-4 py-1 border-b last:border-0 border-slate-100">
          <span :class="{
            'text-green-700': e.type === 'track_matched',
            'text-yellow-700': e.type === 'track_unmatched',
            'text-blue-700': e.type === 'playlist_started' || e.type === 'playlist_done',
            'text-red-700': e.type === 'error',
          }">
            [{{ e.type }}]
          </span>
          {{ e.playlist_name ? `${e.playlist_name} - ` : '' }}{{ e.track_title ?? e.message ?? '' }}
        </li>
      </ul>
    </div>
  </section>
</template>
