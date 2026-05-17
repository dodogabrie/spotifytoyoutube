<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { transfer as transferApi, type JobSnapshot } from '../api/transfer'

const props = defineProps<{ jobId: string }>()
const snapshot = ref<JobSnapshot | null>(null)
const error = ref<string | null>(null)

async function load() {
  try {
    snapshot.value = await transferApi.status(props.jobId)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Failed to load job'
  }
}

onMounted(load)
</script>

<template>
  <section class="space-y-6">
    <header>
      <h1 class="text-2xl font-bold">Transfer complete</h1>
      <p class="text-slate-500 text-sm">Job {{ jobId }}</p>
    </header>

    <div v-if="error" class="text-red-600">{{ error }}</div>

    <div v-if="snapshot" class="grid grid-cols-3 gap-4">
      <div class="rounded-xl border border-slate-200 bg-white p-4">
        <div class="text-xs text-slate-500 uppercase">Matched</div>
        <div class="text-3xl font-bold text-emerald-600 mt-1">{{ snapshot.matched }}</div>
      </div>
      <div class="rounded-xl border border-slate-200 bg-white p-4">
        <div class="text-xs text-slate-500 uppercase">Unmatched</div>
        <div class="text-3xl font-bold text-amber-600 mt-1">{{ snapshot.unmatched }}</div>
      </div>
      <div class="rounded-xl border border-slate-200 bg-white p-4">
        <div class="text-xs text-slate-500 uppercase">Skipped</div>
        <div class="text-3xl font-bold text-slate-600 mt-1">{{ snapshot.skipped }}</div>
      </div>
    </div>

    <div class="flex gap-3">
      <a
        v-if="snapshot?.report_path"
        :href="transferApi.reportUrl(jobId)"
        class="bg-slate-900 text-white px-4 py-2 rounded"
      >
        Download report JSON
      </a>
      <RouterLink to="/" class="border border-slate-300 px-4 py-2 rounded">Start new transfer</RouterLink>
    </div>
  </section>
</template>
