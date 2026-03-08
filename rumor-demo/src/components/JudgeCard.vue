<template>
  <div
    class="agent-card judge-card"
    :class="[status, { 'judge-active': status === 'collecting', 'card-finished': status === 'done' }]"
  >
    <div class="card-glow judge-glow"></div>

    <div class="agent-header judge-header">
      <img :src="icon" :alt="title" class="agent-icon judge-icon" />
      <div>
        <h3>{{ title }}</h3>
        <p>{{ subtitle }}</p>
      </div>
      <span class="status-badge" :class="status">{{ statusText }}</span>
    </div>

    <div class="judge-content">
      <div class="judge-orb" :class="status">
        <div class="judge-core"></div>
        <span class="judge-wave"></span>
        <span class="judge-wave"></span>
        <span class="judge-wave"></span>
        <span class="judge-wave"></span>

        <div v-if="status !== 'idle'" class="signal-bars">
          <span></span><span></span><span></span>
        </div>
      </div>

      <div class="judge-panel">
        <div v-for="(log, idx) in logs" :key="idx" class="judge-step">
          <span class="judge-step-index">{{ idx + 1 }}</span>
          <span>{{ log }}</span>
        </div>

        <div v-if="!logs.length" class="log-placeholder">等待三份证据汇聚后启动...</div>

        <transition name="fade-up">
          <VerdictBox v-if="status === 'done'" :verdict="verdict" />
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VerdictBox from './VerdictBox.vue'

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
  },
  verdict: {
    type: Object,
    default: () => ({
      verdict: '',
      category: '',
      confidence: 0,
      reasoning: ''
    })
  }
})

const statusText = computed(() => {
  const map = {
    idle: '待命',
    collecting: '分析中',
    done: '已完成'
  }
  return map[props.status] || '待命'
})
</script>