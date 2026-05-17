import { api } from './client'

export interface AuthStatus {
  spotify_connected: boolean
  ytmusic_connected: boolean
}

export interface YTMusicStart {
  verification_url: string
  user_code: string
  interval: number
  expires_in: number
}

export interface YTMusicPoll {
  status: 'pending' | 'authorized' | 'expired' | 'denied' | 'error'
  error: string | null
}

export const auth = {
  status: () => api.get<AuthStatus>('/auth/ytmusic/status').then((r) => r.data),
  spotifyLoginUrl: () => '/api/auth/spotify/login',
  spotifyLogout: () => api.post('/auth/spotify/logout'),
  ytmusicStart: () => api.post<YTMusicStart>('/auth/ytmusic/start').then((r) => r.data),
  ytmusicPoll: () => api.post<YTMusicPoll>('/auth/ytmusic/poll').then((r) => r.data),
  ytmusicLogout: () => api.post('/auth/ytmusic/logout'),
}
