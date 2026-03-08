<template>
  <div
    class="agent-card evidence-card"
    :class="[status, { 'card-active': status === 'collecting', 'card-finished': status === 'done' }]"
  >
    <div class="card-glow"></div>

    <div class="agent-header">
      <img :src="icon" :alt="title" class="agent-icon" />
      <div>
        <h3>{{ title }}</h3>
        <p>{{ subtitle }}</p>
      </div>
      <span class="status-badge" :class="status">{{ statusText }}</span>
    </div>

    <div class="agent-body">
      <div class="orbital-area" :class="status">
        <div class="core-dot"></div>
        <span class="orbit orbit-a"></span>
        <span class="orbit orbit-a orbit-delay-1"></span>
        <span class="orbit orbit-a orbit-delay-2"></span>
        <span class="orbit orbit-b"></span>
        <span class="orbit orbit-b orbit-delay-3"></span>
        <span v-if="status === 'done'" class="success-ring"></span>
      </div>

      <div class="logs">
        <div
          v-for="(log, idx) in logs"
          :key="idx"
          class="log-item"
          :class="{ active: idx === logs.length - 1 && status === 'collecting' }"
        >
          <span class="log-dot"></span>
          <span>{{ log }}</span>
        </div>
        <div v-if="!logs.length" class="log-placeholder">等待任务开始...</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  },
  icon: {
    type: String,
    default: ''
  },
  status: {
    type: String,
    default: 'idle'
  },
  logs: {
    type: Array,
    default: () => []
  }
})

const statusText = computed(() => {
  const map = {
    idle: '待命',
    collecting: '收集中',
    done: '已完成'
  }
  return map[props.status] || '待命'
})
</script>