<template>
  <div class="page detect-page">
    <div class="detect-shell">
      <div class="detect-toolbar">
        <el-button text class="back-link" @click="goHome">← 返回首页</el-button>
      </div>

      <el-card shadow="never" class="input-card">
        <template #header>
          <div class="section-title">新闻输入</div>
        </template>

        <el-form label-position="top" class="detect-form">
          <div class="input-shell">
            <div class="input-panel input-panel--text compact-panel">
              <div class="input-panel__label">新闻标题</div>
              <el-form-item class="title-form-item">
                <el-input
                  v-model="title"
                  type="textarea"
                  :rows="7"
                  resize="none"
                  placeholder="请输入新闻标题，例如：某地突发重大事件，现场图片曝光..."
                />
              </el-form-item>
        
            </div>

            <div class="input-panel input-panel--media compact-panel">
              <div class="input-panel__label">新闻图片</div>

              <div class="media-grid compact-media-grid">
                <el-upload
                  ref="uploadRef"
                  class="custom-upload"
                  drag
                  action="#"
                  :auto-upload="false"
                  :show-file-list="false"
                  :before-upload="beforeUpload"
                  :on-change="handleUploadChange"
                  accept="image/*"
                >
                  <div class="upload-inner">
                    <div class="upload-title">
                      {{ imagePreview ? '重新选择图片' : '点击或拖拽上传图片' }}
                    </div>
                    <div class="upload-desc">支持 jpg / png / webp 等常见格式</div>
                  </div>
                </el-upload>

                <div class="image-preview-wrap" :class="{ 'is-empty': !imagePreview }">
                  <template v-if="imagePreview">
                    <button
                      type="button"
                      class="preview-remove"
                      aria-label="移除图片"
                      @click.stop="clearSelectedImage"
                    >
                      ×
                    </button>
                    <img :src="imagePreview" alt="preview" class="image-preview" />
                    <div class="image-preview-caption">{{ imageFile?.name || '已选择图片' }}</div>
                  </template>

                  <div v-else class="image-preview-empty">
                    <div class="image-preview-empty__title">完整预览区</div>
                    <div class="image-preview-empty__desc">上传后会按原始比例完整展示图片</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="input-panel input-panel--actions compact-panel">
              <div class="input-panel__label">操作面板</div>
              <div class="action-panel">
                <div class="action-panel__status">
                  <div class="action-panel__status-label">当前状态</div>
                  <div class="action-panel__status-value">{{ running ? '分析执行中' : canStart ? '可以开始检测' : '等待补全输入' }}</div>
                  <div class="action-panel__status-desc">
                    {{ running ? '请稍候，系统正在并行收集三路证据。' : '上传图片并填写标题后，即可开始完整检测。' }}
                  </div>
                </div>

                <el-button
                  type="primary"
                  size="large"
                  class="action-panel__button action-panel__button--primary"
                  :disabled="!canStart || running"
                  @click="startDetection"
                >
                  {{ running ? '分析进行中...' : '开始分析检测' }}
                </el-button>
                <el-button
                  size="large"
                  class="action-panel__button action-panel__button--ghost"
                  :disabled="running"
                  @click="resetAll"
                >
                  重置全部
                </el-button>
              </div>
            </div>
          </div>
        </el-form>
      </el-card>

      <div class="agents-top">
        <AgentCard
          v-for="agent in evidenceAgents"
          :key="agent.key"
          :title="agent.title"
          :subtitle="agent.subtitle"
          :icon="agent.icon"
          :status="agent.status"
          :verdict="agent.verdict"
          :confidence="agent.confidence"
          :excerpt="agent.excerpt"
          :report-sections="agent.reportSections"
        />
      </div>

      <FlowConnector
        :left-active="evidenceAgents[0].status !== 'idle'"
        :middle-active="evidenceAgents[1].status !== 'idle'"
        :right-active="evidenceAgents[2].status !== 'idle'"
        :merge-active="judge.status !== 'idle'"
      />

      <div class="judge-wrap">
        <JudgeCard
          :title="judge.title"
          :subtitle="judge.subtitle"
          :icon="judge.icon"
          :status="judge.status"
          :logs="judge.logs"
          :verdict="verdict"
          :can-export="canExportReport"
          :can-preview="canViewReport"
          @view-report="openReportDialog"
          @download-report="downloadReport"
        />
      </div>
    </div>

    <el-dialog
      v-model="reportDialogVisible"
      class="report-preview-dialog"
      width="92vw"
      top="4vh"
      destroy-on-close
    >
      <template #header>
        <div class="report-preview-dialog__header">
          <div>
            <div class="report-preview-dialog__eyebrow">完整检测报告</div>
            <div class="report-preview-dialog__title">{{ title || '未命名检测任务' }}</div>
          </div>
          <el-button type="primary" :disabled="exporting" @click="downloadReport">
            {{ exporting ? '导出中...' : '下载 PDF 报告' }}
          </el-button>
        </div>
      </template>

      <div class="report-preview-dialog__body">
        <ReportDocument :report="reportSnapshot" />
      </div>
    </el-dialog>

    <div class="pdf-report-stage" aria-hidden="true">
      <ReportDocument ref="reportExportRef" :report="reportSnapshot" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import AgentCard from '../components/AgentCard.vue'
import JudgeCard from '../components/JudgeCard.vue'
import FlowConnector from '../components/FlowConnector.vue'
import ReportDocument from '../components/ReportDocument.vue'
import { useDetectionDemo } from '../composables/useDetectionDemo'
import { createReportSnapshot, exportReportPdf } from '../utils/reportExport'

const router = useRouter()

const title = ref('')
const imageFile = ref(null)
const imagePreview = ref('')
const uploadRef = ref(null)
const reportExportRef = ref(null)
const exporting = ref(false)
const reportDialogVisible = ref(false)

const { running, evidenceAgents, judge, verdict, meta, startDemo, resetDemo } = useDetectionDemo()

const canStart = computed(() => title.value.trim().length > 0 && !!imageFile.value)
const canExportReport = computed(() => judge.status === 'done' && Boolean(verdict.verdict) && !exporting.value)
const canViewReport = computed(() => judge.status === 'done' && Boolean(verdict.verdict))
const reportSnapshot = computed(() =>
  createReportSnapshot({
    title: title.value,
    meta,
    judge,
    verdict,
    evidenceAgents
  })
)

function goHome() {
  router.push('/')
}

function beforeUpload() {
  return false
}

function revokePreview() {
  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value)
  }
}

function clearSelectedImage(resetState = true) {
  imageFile.value = null
  revokePreview()
  imagePreview.value = ''
  uploadRef.value?.clearFiles?.()

  if (resetState) {
    resetDemo()
  }
}

function handleUploadChange(uploadFile) {
  const raw = uploadFile.raw
  if (!raw) return

  revokePreview()
  imageFile.value = raw
  imagePreview.value = URL.createObjectURL(raw)
  resetDemo()
}

async function startDetection() {
  if (!canStart.value) {
    ElMessage.warning('请先输入新闻标题并上传图片')
    return
  }

  await startDemo({
    title: title.value,
    imageFile: imageFile.value
  })
}

async function downloadReport() {
  if (!canExportReport.value) return

  const element = reportExportRef.value?.$el || reportExportRef.value
  if (!element) {
    ElMessage.error('PDF 报告容器未准备好')
    return
  }

  exporting.value = true

  try {
    await nextTick()
    await exportReportPdf(element, title.value)
    ElMessage.success('PDF 检测报告已开始下载')
  } catch (error) {
    console.error('Failed to export PDF report:', error)
    ElMessage.error('PDF 导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

function openReportDialog() {
  if (!canViewReport.value) return
  reportDialogVisible.value = true
}

function resetAll() {
  title.value = ''
  clearSelectedImage(false)
  resetDemo()
  reportDialogVisible.value = false
}

onBeforeUnmount(() => {
  clearSelectedImage(false)
})
</script>
