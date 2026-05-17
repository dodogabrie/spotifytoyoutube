<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { playlists as playlistsApi, type PlaylistDTO } from '../api/playlists'
import { transfer as transferApi, type IdempotencyMode } from '../api/transfer'
import { useTransferStore } from '../stores/transfer'

const router = useRouter()
const store = useTransferStore()
const items = ref<PlaylistDTO[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const filter = ref('')
const selected = ref<Set<string>>(new Set())
const submitting = ref(false)

const filtered = computed(() => {
  if (!filter.value.trim()) return items.value
  const f = filter.value.toLowerCase()
  return items.value.filter((p) => p.name.toLowerCase().includes(f))
})

const allFilteredSelected = computed(
  () => filtered.value.length > 0 && filtered.value.every((p) => selected.value.has(p.id))
)

function toggle(id: string) {
  const next = new Set(selected.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selected.value = next
}

function toggleAll() {
  const next = new Set(selected.value)
  if (allFilteredSelected.value) {
    filtered.value.forEach((p) => next.delete(p.id))
  } else {
    filtered.value.forEach((p) => next.add(p.id))
  }
  selected.value = next
}

async function load() {
  loading.value = true
  error.value = null
  try {
    items.value = await playlistsApi.list(store.sourceProvider() as 'spotify' | 'ytmusic')
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Failed to load playlists'
  } finally {
    loading.value = false
  }
}

async function startTransfer() {
  if (selected.value.size === 0) return
  submitting.value = true
  try {
    const ids = Array.from(selected.value)
    store.setSelection(items.value.filter((p) => selected.value.has(p.id)))
    const { job_id } = await transferApi.start({
      direction: store.direction,
      playlist_ids: ids,
      idempotency: store.idempotency,
    })
    router.push(`/transfer/${job_id}`)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Failed to start transfer'
  } finally {
    submitting.value = false
  }
}

onMounted(load)

const idempotencyOptions: { value: IdempotencyMode; label: string }[] = [
  { value: 'create_new', label: 'Create new (suffix on collision)' },
  { value: 'append', label: 'Append to existing' },
  { value: 'replace', label: 'Replace existing (wipe + refill)' },
  { value: 'skip_if_exists', label: 'Skip if exists' },
]
</script>

<template>
  <section class="space-y-6">
    <header class="flex items-baseline justify-between">
      <div>
        <h1 class="text-2xl font-bold">Pick source playlists</h1>
        <p class="text-slate-500 text-sm">From {{ store.sourceProvider() }} → to {{ store.targetProvider() }}</p>
      </div>
      <div class="text-sm text-slate-500">{{ selected.size }} selected</div>
    </header>

    <div class="rounded-xl border border-slate-200 bg-white p-4 grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
      <input
        v-model="filter"
        placeholder="Filter playlists by name"
        class="border border-slate-300 rounded px-3 py-2 col-span-2"
      />
      <select v-model="store.idempotency" class="border border-slate-300 rounded px-3 py-2">
        <option v-for="opt in idempotencyOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
    </div>

    <div v-if="loading" class="text-slate-500">Loading…</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>
    <div v-else class="rounded-xl border border-slate-200 bg-white">
      <div class="px-4 py-2 border-b border-slate-200 flex items-center gap-3 text-sm">
        <label class="flex items-center gap-2">
          <input type="checkbox" :checked="allFilteredSelected" @change="toggleAll" />
          <span>Select all ({{ filtered.length }})</span>
        </label>
      </div>
      <ul class="divide-y divide-slate-200">
        <li v-for="p in filtered" :key="p.id" class="px-4 py-3 flex items-center gap-3">
          <input type="checkbox" :checked="selected.has(p.id)" @change="toggle(p.id)" />
          <div class="flex-1">
            <div class="font-medium">{{ p.name }}</div>
            <div class="text-xs text-slate-500">{{ p.track_count ?? '?' }} tracks</div>
          </div>
        </li>
        <li v-if="filtered.length === 0" class="px-4 py-6 text-slate-400 text-center">No playlists.</li>
      </ul>
    </div>

    <button
      class="bg-slate-900 text-white px-5 py-2 rounded disabled:opacity-40"
      :disabled="selected.size === 0 || submitting"
      @click="startTransfer"
    >
      Transfer {{ selected.size }} playlist(s)
    </button>
  </section>
</template>
