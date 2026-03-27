import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import DetectionView from '../views/DetectionView.vue'
import KnowledgeView from '../views/KnowledgeView.vue'
import HistoryView from '../views/HistoryView.vue'
import ManualView from '../views/ManualView.vue'

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
  },
  {
    path: '/knowledge',
    name: 'knowledge',
    component: KnowledgeView
  },
  {
    path: '/history',
    name: 'history',
    component: HistoryView
  },
  {
    path: '/manual',
    name: 'manual',
    component: ManualView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
