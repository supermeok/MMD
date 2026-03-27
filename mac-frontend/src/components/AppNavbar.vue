<template>
  <header class="app-navbar">
    <button type="button" class="app-navbar__brand" @click="goTo('/')">
      <span class="app-navbar__brand-dot"></span>
      <span class="app-navbar__brand-text">
        <strong>MAC-Judge</strong>
        <small>基于多智能体裁决的谣言检测系统</small>
      </span>
    </button>

    <nav class="app-navbar__links">
      <button
        v-for="item in navItems"
        :key="item.path"
        type="button"
        class="app-navbar__link"
        :class="{ 'is-active': isActive(item.path) }"
        @click="goTo(item.path)"
      >
        {{ item.label }}
      </button>
    </nav>
  </header>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const navItems = [
  { label: '首页', path: '/' },
  { label: '开始检测', path: '/detect' },
  { label: '知识库', path: '/knowledge' },
  { label: '历史记录', path: '/history' },
  { label: '系统手册', path: '/manual' }
]

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

function goTo(path) {
  if (route.path === path) return
  router.push(path)
}
</script>
