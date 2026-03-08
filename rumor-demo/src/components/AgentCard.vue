<template>
  <el-card
    shadow="never"
    class="agent-card unified-card"
    :class="[status, { 'is-running': status === 'collecting', 'is-done': status === 'done' }]"
  >
    <div class="card-shine"></div>

    <div class="agent-card__header">
      <div class="agent-card__meta">
        <div class="agent-card__icon-wrap">
          <img :src="icon" :alt="title" class="agent-card__icon" />
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

    <div class="agent-card__body">
      <div class="agent-orbit" :class="status">
        <div class="agent-orbit__core"></div>
        <span class="agent-orbit__ring ring-1"></span>
        <span class="agent-orbit__ring ring-2"></span>
        <span class="agent-orbit__ring ring-3"></span>
        <span v-if="status === 'done'" class="agent-orbit__success"></span>
      </div>

      <div class="agent-card__logs">
        <div
          v-for="(log, idx) in logs"
          :key="idx"
          class="agent-log"
          :class="{ active: idx === logs.length - 1 && status === 'collecting' }"
        >
          <span class="agent-log__dot"></span>
          <span class="agent-log__text">{{ log }}</span>
        </div>

        <div v-if="!logs.length" class="agent-log agent-log--placeholder">
          <span class="agent-log__dot"></span>
          <span class="agent-log__text">等待任务开始...</span>
        </div>
      </div>
    </div>
  </el-card>
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

const tagType = computed(() => {
  const map = {
    idle: 'info',
    collecting: 'primary',
    done: 'success'
  }
  return map[props.status] || 'info'
})
</script>