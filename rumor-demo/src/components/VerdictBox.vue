<template>
  <div class="verdict-box">
    <div class="verdict-title">裁决结果</div>
    <div class="verdict-main">{{ verdict.verdict }}</div>
    <div class="verdict-meta">
      <span>类别：{{ verdict.category }}</span>
      <span>置信度：{{ verdict.confidence }}%</span>
    </div>
    <p>{{ verdict.reasoning }}</p>
  </div>
</template>

<script setup>
defineProps({
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
</script>