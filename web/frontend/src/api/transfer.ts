import { api } from './client'

export type Direction = 'spotify_to_ytmusic' | 'ytmusic_to_spotify'
export type IdempotencyMode = 'create_new' | 'append' | 'replace' | 'skip_if_exists'

export interface TransferRequest {
  direction: Direction
  playlist_ids: string[]
  idempotency: IdempotencyMode
}

export interface JobSnapshot {
  job_id: string
  status: 'queued' | 'running' | 'done' | 'error'
  direction: Direction
  idempotency: IdempotencyMode
  last_events: Array<Record<string, unknown>>
  matched: number
  unmatched: number
  skipped: number
  report_path: string | null
  error: string | null
}

export const transfer = {
  start: (req: TransferRequest) =>
    api.post<{ job_id: string }>('/transfer', req).then((r) => r.data),
  status: (jobId: string) =>
    api.get<JobSnapshot>(`/transfer/${jobId}`).then((r) => r.data),
  reportUrl: (jobId: string) => `/api/transfer/${jobId}/report`,
  streamUrl: (jobId: string) => {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    return `${proto}://${window.location.host}/api/transfer/${jobId}/stream`
  },
}
