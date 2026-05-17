import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Direction, IdempotencyMode } from '../api/transfer'
import type { PlaylistDTO } from '../api/playlists'

export const useTransferStore = defineStore('transfer', () => {
  const direction = ref<Direction>('spotify_to_ytmusic')
  const idempotency = ref<IdempotencyMode>('create_new')
  const selectedIds = ref<string[]>([])
  const selectedPlaylists = ref<PlaylistDTO[]>([])

  function setSelection(playlists: PlaylistDTO[]) {
    selectedPlaylists.value = playlists
    selectedIds.value = playlists.map((p) => p.id)
  }

  function sourceProvider() {
    return direction.value === 'spotify_to_ytmusic' ? 'spotify' : 'ytmusic'
  }

  function targetProvider() {
    return direction.value === 'spotify_to_ytmusic' ? 'ytmusic' : 'spotify'
  }

  return { direction, idempotency, selectedIds, selectedPlaylists, setSelection, sourceProvider, targetProvider }
})
