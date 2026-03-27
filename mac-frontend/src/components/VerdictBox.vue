<template>
  <div class="verdict-box">
    <div class="verdict-head">
      <div class="verdict-title">裁决结果</div>
      <div class="verdict-actions">
        <el-button text class="verdict-export-btn" :disabled="!canPreview" @click="$emit('view-report')">
          查看报告
        </el-button>
        <el-button text class="verdict-export-btn" :disabled="!canExport" @click="$emit('download-report')">
          导出 PDF
        </el-button>
      </div>
    </div>
    <div class="verdict-main">{{ verdict.verdict }}</div>

    <el-space wrap class="verdict-meta">
      <el-tag type="danger" effect="dark">类别：{{ verdict.category }}</el-tag>
      <el-tag type="success" effect="dark">置信度：{{ verdict.confidence }}%</el-tag>
    </el-space>

    <p>{{ verdict.reasoning }}</p>
  </div>
</template>

<script setup>
defineEmits(['download-report', 'view-report'])

defineProps({
  verdict: {
    type: Object,
    default: () => ({
      verdict: '',
      category: '',
      confidence: 0,
      reasoning: ''
    })
  },
  canExport: {
    type: Boolean,
    default: false
  },
  canPreview: {
    type: Boolean,
    default: false
  }
})
</script>
