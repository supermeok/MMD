<template>
  <div ref="chartRef" class="echarts-panel" :style="{ height }"></div>
</template>

<script setup>
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  height: {
    type: String,
    default: '320px'
  },
  options: {
    type: Object,
    default: () => ({})
  }
})

const chartRef = ref(null)
let chartInstance = null
let resizeObserver = null

function renderChart() {
  if (!chartRef.value) {
    return
  }

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  chartInstance.setOption(props.options, true)
}

function resizeChart() {
  chartInstance?.resize()
}

onMounted(() => {
  renderChart()

  if (typeof ResizeObserver !== 'undefined' && chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      resizeChart()
    })
    resizeObserver.observe(chartRef.value)
  } else {
    window.addEventListener('resize', resizeChart)
  }
})

watch(
  () => props.options,
  () => {
    renderChart()
  },
  { deep: true }
)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  window.removeEventListener('resize', resizeChart)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped>
.echarts-panel {
  width: 100%;
}
</style>
