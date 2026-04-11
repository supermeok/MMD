<template>
  <div class="page analytics-page portal-page">
    <div class="portal-shell">
      <AppNavbar />

      <section class="page-intro">
        <div>
          <div class="page-intro__eyebrow">Dataset Analytics</div>
          <h1>样本数据看板</h1>
        </div>
      </section>

      <section v-loading="loading" class="portal-overview-cards analytics-overview-grid">
        <article class="portal-overview-card is-emphasis">
          <span>总样本数</span>
          <strong>{{ datasetOverview.total }}</strong>
        </article>
        <article class="portal-overview-card">
          <span>来源目录</span>
          <strong>{{ datasetOverview.folderTotal }}</strong>
        </article>
        <article class="portal-overview-card">
          <span>虚假样本</span>
          <strong>{{ datasetOverview.fakeTotal }}</strong>
        </article>
        <article class="portal-overview-card">
          <span>真实样本</span>
          <strong>{{ datasetOverview.realTotal }}</strong>
        </article>
        <article class="portal-overview-card">
          <span>历史检测</span>
          <strong>{{ historyOverview.total }}</strong>
        </article>
        <article class="portal-overview-card">
          <span>待复查</span>
          <strong>{{ historyOverview.pendingReview }}</strong>
        </article>
      </section>

      <section class="portal-section">
        <div v-loading="loading" class="portal-chart-grid">
          <article class="portal-chart-card tech-card">
            <div class="portal-chart-card__head">
              <div>
                <span>真假分布</span>
                <strong>{{ datasetOverview.total }}</strong>
              </div>
              <small>目录样本</small>
            </div>
            <EchartsPanel :options="splitOption" />
          </article>

          <article class="portal-chart-card tech-card">
            <div class="portal-chart-card__head">
              <div>
                <span>主题细分</span>
                <strong>{{ themeStats.length }}</strong>
              </div>
              <small>内容主题</small>
            </div>
            <EchartsPanel :options="themeOption" />
          </article>

          <article class="portal-chart-card tech-card">
            <div class="portal-chart-card__head">
              <div>
                <span>伪造方式</span>
                <strong>{{ techniqueStats.length }}</strong>
              </div>
              <small>命名模式</small>
            </div>
            <EchartsPanel :options="techniqueOption" />
          </article>

          <article class="portal-chart-card tech-card">
            <div class="portal-chart-card__head">
              <div>
                <span>历史复查状态</span>
                <strong>{{ historyOverview.total }}</strong>
              </div>
              <small>检测归档</small>
            </div>
            <EchartsPanel :options="historyOption" />
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import AppNavbar from '../components/AppNavbar.vue'
import EchartsPanel from '../components/EchartsPanel.vue'
import { getDatasetAnalytics, getHistorySummary } from '../api'

const loading = ref(false)
const datasetOverview = reactive({
  total: 0,
  fakeTotal: 0,
  realTotal: 0,
  folderTotal: 0
})
const historyOverview = reactive({
  total: 0,
  pendingReview: 0,
  approvedCount: 0,
  correctedCount: 0,
  flaggedCount: 0
})
const stats = reactive({
  theme: {},
  technique: {}
})

const chartTextColor = '#dce7ff'
const chartSubtextColor = '#8fa5d2'
const chartAxisLineColor = 'rgba(143, 165, 210, 0.18)'
const themePalette = ['#45c7ff', '#7f6bff', '#25d6a2', '#ff9b57', '#ff6287', '#ffd166', '#60a5fa']
const splitPalette = ['#ff6287', '#45c7ff']
const techniquePalette = ['#7f6bff', '#45c7ff', '#25d6a2', '#ff9b57', '#ffd166', '#ff6287']
const historyPalette = ['#45c7ff', '#25d6a2', '#ff9b57', '#ff6287']

const themeStats = computed(() => sortStats(stats.theme))
const techniqueStats = computed(() => sortStats(stats.technique))

const splitOption = computed(() => ({
  color: splitPalette,
  tooltip: { trigger: 'item' },
  legend: {
    bottom: 0,
    icon: 'circle',
    textStyle: { color: chartSubtextColor }
  },
  series: [
    {
      type: 'pie',
      radius: ['48%', '72%'],
      center: ['50%', '44%'],
      label: {
        color: chartTextColor,
        formatter: '{b}\n{c}'
      },
      labelLine: {
        lineStyle: { color: 'rgba(220, 231, 255, 0.28)' }
      },
      itemStyle: {
        borderRadius: 10,
        borderColor: '#0d1730',
        borderWidth: 2
      },
      data: [
        { name: '虚假样本', value: datasetOverview.fakeTotal },
        { name: '真实样本', value: datasetOverview.realTotal }
      ]
    }
  ]
}))

const themeOption = computed(() => ({
  color: themePalette,
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' }
  },
  grid: {
    top: 14,
    right: 18,
    bottom: 16,
    left: 110
  },
  xAxis: {
    type: 'value',
    axisLabel: { color: chartSubtextColor },
    splitLine: { lineStyle: { color: chartAxisLineColor } }
  },
  yAxis: {
    type: 'category',
    data: themeStats.value.map((item) => item.name),
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: chartTextColor }
  },
  series: [
    {
      type: 'bar',
      data: themeStats.value.map((item) => item.value),
      barWidth: 16,
      itemStyle: {
        borderRadius: 999,
        color: (params) => themePalette[params.dataIndex % themePalette.length]
      }
    }
  ]
}))

const techniqueOption = computed(() => ({
  color: techniquePalette,
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' }
  },
  grid: {
    top: 24,
    right: 18,
    bottom: 48,
    left: 28,
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: techniqueStats.value.map((item) => item.name),
    axisLine: { lineStyle: { color: chartAxisLineColor } },
    axisTick: { show: false },
    axisLabel: {
      color: chartSubtextColor,
      interval: 0,
      rotate: 12
    }
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: chartSubtextColor },
    splitLine: { lineStyle: { color: chartAxisLineColor } }
  },
  series: [
    {
      type: 'bar',
      barMaxWidth: 54,
      data: techniqueStats.value.map((item) => item.value),
      itemStyle: {
        borderRadius: [12, 12, 0, 0],
        color: (params) => techniquePalette[params.dataIndex % techniquePalette.length]
      }
    }
  ]
}))

const historyOption = computed(() => ({
  color: historyPalette,
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' }
  },
  grid: {
    top: 24,
    right: 16,
    bottom: 32,
    left: 24,
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: ['待复查', '已通过', '人工改判', '已标记'],
    axisLine: {
      lineStyle: {
        color: chartAxisLineColor
      }
    },
    axisTick: {
      show: false
    },
    axisLabel: {
      color: chartSubtextColor
    }
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      color: chartSubtextColor
    },
    splitLine: {
      lineStyle: {
        color: chartAxisLineColor
      }
    }
  },
  series: [
    {
      type: 'bar',
      barMaxWidth: 42,
      data: [
        historyOverview.pendingReview,
        historyOverview.approvedCount,
        historyOverview.correctedCount,
        historyOverview.flaggedCount
      ],
      itemStyle: {
        borderRadius: [12, 12, 0, 0],
        color: (params) => historyPalette[params.dataIndex % historyPalette.length]
      }
    }
  ]
}))

function sortStats(input = {}) {
  return Object.entries(input)
    .filter(([, value]) => Number(value) > 0)
    .sort((a, b) => b[1] - a[1])
    .map(([name, value]) => ({ name, value }))
}

async function loadAnalytics() {
  loading.value = true
  try {
    const [datasetResponse, historyResponse] = await Promise.all([
      getDatasetAnalytics(),
      getHistorySummary()
    ])

    datasetOverview.total = datasetResponse?.total || 0
    datasetOverview.fakeTotal = datasetResponse?.fake_total || 0
    datasetOverview.realTotal = datasetResponse?.real_total || 0
    datasetOverview.folderTotal = datasetResponse?.folder_total || 0
    stats.theme = datasetResponse?.theme_stats || {}
    stats.technique = datasetResponse?.technique_stats || {}

    historyOverview.total = historyResponse?.total || 0
    historyOverview.pendingReview = historyResponse?.pending_review || 0
    historyOverview.approvedCount = historyResponse?.approved_count || 0
    historyOverview.correctedCount = historyResponse?.corrected_count || 0
    historyOverview.flaggedCount = historyResponse?.flagged_count || 0
  } catch (error) {
    console.error('Failed to load dataset analytics:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAnalytics()
})
</script>
