import { api } from './client'

export type Provider = 'spotify' | 'ytmusic'

export interface PlaylistDTO {
  id: string
  name: string
  description: string | null
  track_count: number | null
  public: boolean | null
  collaborative: boolean
}

export const playlists = {
  list: (provider: Provider) =>
    api.get<PlaylistDTO[]>('/playlists', { params: { provider } }).then((r) => r.data),
}
