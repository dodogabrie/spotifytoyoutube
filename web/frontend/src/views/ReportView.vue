<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { transfer as transferApi, type JobSnapshot } from '../api/transfer'
import AppButton from '../components/AppButton.vue'
import PageHeader from '../components/PageHeader.vue'
import StatTile from '../components/StatTile.vue'

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
  <section class="space-y-6 sm:space-y-8">
    <PageHeader title="Transfer complete" :subtitle="`Job ${jobId}`" />

    <div
      v-if="error"
      class="rounded-card border border-danger-200 bg-danger-50 text-danger-700 text-sm px-4 py-3"
    >
      {{ error }}
    </div>

    <div v-if="snapshot" class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <StatTile label="Matched" :value="snapshot.matched" tone="success" />
      <StatTile label="Unmatched" :value="snapshot.unmatched" tone="warning" />
      <StatTile label="Skipped" :value="snapshot.skipped" tone="muted" />
    </div>

    <div class="flex flex-col sm:flex-row gap-3">
      <a
        v-if="snapshot?.report_path"
        :href="transferApi.reportUrl(jobId)"
        class="inline-flex items-center justify-center gap-2 font-medium px-5 py-2.5 rounded-control bg-accent-900 text-white hover:bg-accent-800 shadow-card"
      >
        Download report JSON
      </a>
      <RouterLink to="/">
        <AppButton tone="ghost">Start new transfer</AppButton>
      </RouterLink>
    </div>
  </section>
</template>
