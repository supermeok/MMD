import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import DetectionView from '../views/DetectionView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/detect',
    name: 'detect',
    component: DetectionView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router