import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import DetectionView from '../views/DetectionView.vue'
import KnowledgeView from '../views/KnowledgeView.vue'
import AnalyticsView from '../views/AnalyticsView.vue'
import HistoryView from '../views/HistoryView.vue'
import ManualView from '../views/ManualView.vue'
import LoginView from '../views/LoginView.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginView
  },
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
    path: '/analytics',
    name: 'analytics',
    component: AnalyticsView
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
