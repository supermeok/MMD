<template>
  <div class="verdict-box">
    <div class="verdict-title">裁决结果</div>
    <div class="verdict-main">{{ verdict.verdict }}</div>

    <el-space wrap class="verdict-meta">
      <el-tag type="danger" effect="dark">类别：{{ verdict.category }}</el-tag>
      <el-tag type="success" effect="dark">置信度：{{ verdict.confidence }}%</el-tag>
    </el-space>

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