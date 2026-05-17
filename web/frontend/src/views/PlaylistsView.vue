<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { playlists as playlistsApi, type PlaylistDTO } from '../api/playlists'
import { transfer as transferApi, type IdempotencyMode } from '../api/transfer'
import { useTransferStore } from '../stores/transfer'
import AppCard from '../components/AppCard.vue'
import AppButton from '../components/AppButton.vue'
import PageHeader from '../components/PageHeader.vue'

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

const sourceLabel = computed(() => (store.sourceProvider() === 'spotify' ? 'Spotify' : 'YouTube Music'))
const targetLabel = computed(() => (store.targetProvider() === 'spotify' ? 'Spotify' : 'YouTube Music'))
</script>

<template>
  <section class="space-y-6 sm:space-y-8">
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
      <PageHeader
        title="Pick source playlists"
        :subtitle="`From ${sourceLabel} → to ${targetLabel}`"
      />
      <div class="text-sm text-fg-secondary">
        <span class="font-semibold text-fg-primary tabular-nums">{{ selected.size }}</span> selected
      </div>
    </div>

    <AppCard padding="sm">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
        <div class="md:col-span-2 relative">
          <input
            v-model="filter"
            placeholder="Filter playlists by name"
            class="w-full border border-border rounded-control bg-surface px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-info-500 focus:border-info-500"
          />
        </div>
        <select
          v-model="store.idempotency"
          class="w-full border border-border rounded-control bg-surface px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-info-500 focus:border-info-500"
        >
          <option v-for="opt in idempotencyOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>
    </AppCard>

    <div v-if="loading" class="text-fg-secondary">Loading playlists…</div>
    <div
      v-else-if="error"
      class="rounded-card border border-danger-200 bg-danger-50 text-danger-700 text-sm px-4 py-3"
    >
      {{ error }}
    </div>
    <AppCard v-else padding="sm">
      <div class="px-1 sm:px-2 py-2 flex items-center gap-3 text-sm border-b border-divider">
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            class="h-4 w-4 rounded border-border accent-spotify-600"
            :checked="allFilteredSelected"
            @change="toggleAll"
          />
          <span>Select all ({{ filtered.length }})</span>
        </label>
      </div>
      <ul class="divide-y divide-divider">
        <li
          v-for="p in filtered"
          :key="p.id"
          class="flex items-center gap-3 py-3 px-1 sm:px-2 hover:bg-surface-muted/60 transition rounded"
        >
          <input
            type="checkbox"
            class="h-4 w-4 rounded border-border accent-spotify-600"
            :checked="selected.has(p.id)"
            @change="toggle(p.id)"
          />
          <div class="flex-1 min-w-0">
            <div class="font-medium truncate">{{ p.name }}</div>
            <div class="text-xs text-fg-secondary">
              {{ p.track_count ?? '?' }} tracks
              <span v-if="p.collaborative" class="ml-2 inline-flex items-center px-1.5 py-0.5 rounded bg-info-50 text-info-700 text-[10px] uppercase tracking-wide">
                collab
              </span>
              <span v-else-if="p.public === false" class="ml-2 inline-flex items-center px-1.5 py-0.5 rounded bg-surface-muted text-fg-secondary text-[10px] uppercase tracking-wide">
                private
              </span>
              <span v-else-if="p.public" class="ml-2 inline-flex items-center px-1.5 py-0.5 rounded bg-success-50 text-success-700 text-[10px] uppercase tracking-wide">
                public
              </span>
            </div>
          </div>
        </li>
        <li v-if="filtered.length === 0" class="text-fg-muted text-center py-10">No playlists found.</li>
      </ul>
    </AppCard>

    <div class="flex flex-col sm:flex-row gap-3 sm:items-center">
      <AppButton
        size="lg"
        :disabled="selected.size === 0 || submitting"
        @click="startTransfer"
      >
        Transfer {{ selected.size }} playlist{{ selected.size === 1 ? '' : 's' }}
      </AppButton>
      <span class="text-sm text-fg-muted">
        Target: {{ targetLabel }} · Mode: {{ store.idempotency }}
      </span>
    </div>
  </section>
</template>
