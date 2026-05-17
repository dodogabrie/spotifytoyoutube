import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import LoginView from './views/LoginView.vue'
import PlaylistsView from './views/PlaylistsView.vue'
import TransferView from './views/TransferView.vue'
import ReportView from './views/ReportView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView },
    { path: '/login', component: LoginView },
    { path: '/playlists', component: PlaylistsView },
    { path: '/transfer/:jobId', component: TransferView, props: true },
    { path: '/done/:jobId', component: ReportView, props: true },
  ],
})
