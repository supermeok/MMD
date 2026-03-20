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

      <div class="agent-card__content">
        <div class="agent-card__metrics">
          <div class="agent-metric">
            <span class="agent-metric__label">判定结果</span>
            <strong class="agent-metric__value">{{ displayVerdict }}</strong>
          </div>
          <div class="agent-metric">
            <span class="agent-metric__label">置信度</span>
            <strong class="agent-metric__value">{{ displayConfidence }}</strong>
          </div>
        </div>

        <div class="agent-card__excerpt">
          <div class="agent-card__excerpt-title">模型摘录</div>
          <p>{{ displayExcerpt }}</p>
        </div>

        <div class="agent-card__actions">
          <el-button text class="agent-detail-btn" :disabled="!canViewDetails" @click="dialogVisible = true">
            查看详情
          </el-button>
        </div>
      </div>
    </div>
  </el-card>

  <el-dialog
    v-model="dialogVisible"
    destroy-on-close
    class="agent-report-dialog"
    :title="`${title} · 详细报告`"
    width="760px"
  >
    <div v-if="reportSections.length" class="agent-report">
      <div v-for="(section, idx) in reportSections" :key="`${idx}-${section.title}`" class="agent-report__section">
        <div class="agent-report__title">{{ idx + 1 }}. {{ section.title }}</div>
        <pre class="agent-report__content">{{ section.content }}</pre>
      </div>
    </div>

    <div v-else class="agent-report__empty">暂无详细分析内容。</div>
  </el-dialog>
</template>

<script setup>
import { computed, ref } from 'vue'

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
  verdict: {
    type: String,
    default: ''
  },
  confidence: {
    type: Number,
    default: 0
  },
  excerpt: {
    type: String,
    default: ''
  },
  reportSections: {
    type: Array,
    default: () => []
  }
})

const dialogVisible = ref(false)

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

const displayVerdict = computed(() => {
  if (props.status === 'collecting') return '分析中'
  if (props.status === 'idle') return '等待中'
  return props.verdict || '未返回'
})

const displayConfidence = computed(() => {
  if (props.status !== 'done') return '--'
  return `${props.confidence || 0}%`
})

const displayExcerpt = computed(() => {
  if (props.status === 'collecting') return '正在等待模型返回分析内容...'
  if (props.status === 'idle') return '任务启动后会显示模型返回的关键内容摘录。'
  return props.excerpt || '暂无模型摘录。'
})

const canViewDetails = computed(() => props.status === 'done' && props.reportSections.length > 0)
</script>
