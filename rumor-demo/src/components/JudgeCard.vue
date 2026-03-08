<template>
  <el-card
    shadow="never"
    class="judge-card unified-card"
    :class="[status, { 'is-running': status === 'collecting', 'is-done': status === 'done' }]"
  >
    <div class="card-shine judge-card__shine"></div>

    <div class="agent-card__header">
      <div class="agent-card__meta">
        <div class="agent-card__icon-wrap judge-card__icon-wrap">
          <img :src="icon" :alt="title" class="agent-card__icon judge-card__icon" />
        </div>

        <div class="agent-card__text">
          <h3>{{ title }}</h3>
          <p>{{ subtitle }}</p>
        </div>
      </div>

      <el-tag round effect="dark" :type="tagType" class="agent-card__tag">
        {{ statusText }}
      </el-tag>
    </div>

    <div class="judge-card__body">
      <div class="judge-visual" :class="status">
        <div class="judge-visual__core"></div>
        <span class="judge-visual__wave"></span>
        <span class="judge-visual__wave"></span>
        <span class="judge-visual__wave"></span>

        <div v-if="status !== 'idle'" class="judge-visual__bars">
          <span></span><span></span><span></span>
        </div>
      </div>

      <div class="judge-card__panel">
        <div v-for="(log, idx) in logs" :key="idx" class="judge-step">
          <span class="judge-step__index">{{ idx + 1 }}</span>
          <span class="judge-step__text">{{ log }}</span>
        </div>

        <div v-if="!logs.length" class="judge-step judge-step--placeholder">
          <span class="judge-step__index">·</span>
          <span class="judge-step__text">等待三份证据汇聚后启动...</span>
        </div>

        <transition name="fade-up">
          <VerdictBox v-if="status === 'done'" :verdict="verdict" />
        </transition>
      </div>
    </div>
  </el-card>
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

const tagType = computed(() => {
  const map = {
    idle: 'info',
    collecting: 'warning',
    done: 'success'
  }
  return map[props.status] || 'info'
})
</script>