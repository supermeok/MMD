<template>
  <div class="page detect-page portal-page">
    <div class="portal-shell">
      <AppNavbar />

      <section class="page-intro">
        <div>
          <div class="page-intro__eyebrow">History & Review</div>
          <h1>历史检测记录与人工复查</h1>
        </div>
      </section>

      <section class="portal-overview-cards">
        <article class="portal-overview-card">
          <span>总归档数</span>
          <strong>{{ summary.total || 0 }}</strong>
        </article>
        <article class="portal-overview-card">
          <span>待复查</span>
          <strong>{{ summary.pending_review || 0 }}</strong>
        </article>
        <article class="portal-overview-card is-emphasis">
          <span>人工改判</span>
          <strong>{{ summary.corrected_count || 0 }}</strong>
        </article>
      </section>

      <div class="portal-filter-bar">
        <el-select v-model="filters.review_status" clearable placeholder="筛选复查状态" @change="handleFilter">
          <el-option label="全部状态" value="" />
          <el-option
            v-for="item in reviewStatusOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>

        <el-input
          v-model="filters.search"
          clearable
          placeholder="搜索检测标题..."
          @input="handleSearch"
        />
      </div>

      <div v-loading="loading" class="history-grid">
        <article v-for="item in records" :key="item.id" class="history-card">
          <div class="history-card__image-wrap">
            <img :src="item.image_url" :alt="item.title" class="history-card__image" />
          </div>

          <div class="history-card__body">
            <div class="history-card__meta-row">
              <el-tag size="small" :type="getBinaryTagType(item.auto_verdict)">
                {{ getBinaryLabel(item.auto_verdict) }}
              </el-tag>
              <el-tag size="small" :type="getReviewStatusType(item.review_status)">
                {{ getReviewStatusLabel(item.review_status) }}
              </el-tag>
            </div>

            <h3>{{ item.title }}</h3>
            <div class="history-card__submeta">
              <span>{{ formatDateTime(item.created_at) }}</span>
              <span>{{ getFakeTypeLabel(item.auto_category) }}</span>
              <span>{{ formatConfidence(item.auto_confidence) }}</span>
            </div>
            <p>{{ item.auto_reasoning || '暂无裁决说明。' }}</p>

            <div class="history-card__footer">
              <div class="history-card__reviewer">
                {{ item.reviewer ? `复查人：${item.reviewer}` : '尚未人工复查' }}
              </div>
              <div class="history-card__actions">
                <el-button text class="portal-link-btn" @click="openReview(item)">查看详情</el-button>
                <el-button text class="portal-link-btn" @click="openReportPreview(item)">报告预览</el-button>
                <el-button
                  text
                  type="danger"
                  :loading="deletingId === item.id"
                  @click="handleDelete(item)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </div>
        </article>

        <div v-if="!loading && !records.length" class="portal-empty-state">
          暂无历史记录，请先从“开始检测”页发起一次检测任务。
        </div>
      </div>

      <div class="portal-pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[8, 12, 16, 20]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" width="1240px" destroy-on-close title="审核工作台">
      <div v-if="selectedDetail" class="review-dialog review-dialog--workspace">
        <aside class="audit-sidebar">
          <section class="audit-card audit-card--hero">
            <div class="audit-card__eyebrow">案件概览</div>
            <div class="review-dialog__image-wrap audit-sidebar__image-wrap">
              <img :src="selectedDetail.item.image_url" :alt="selectedDetail.item.title" class="review-dialog__image" />
            </div>

            <div class="audit-sidebar__body">
              <div class="audit-sidebar__tags history-card__meta-row">
                <el-tag size="small" :type="getBinaryTagType(selectedDetail.item.auto_verdict)">
                  {{ getBinaryLabel(selectedDetail.item.auto_verdict) }}
                </el-tag>
                <el-tag size="small" :type="getReviewStatusType(selectedDetail.item.review_status)">
                  {{ getReviewStatusLabel(selectedDetail.item.review_status) }}
                </el-tag>
                <el-tag size="small" :type="getFakeTypeColor(selectedDetail.item.auto_category)">
                  {{ getFakeTypeLabel(selectedDetail.item.auto_category) }}
                </el-tag>
              </div>

              <h3>{{ selectedDetail.item.title }}</h3>
              <p>{{ selectedDetail.item.auto_reasoning || '暂无自动裁决说明。' }}</p>

              <div class="audit-meta-list">
                <div class="audit-meta-item">
                  <span>归档时间</span>
                  <strong>{{ formatDateTime(selectedDetail.item.created_at) }}</strong>
                </div>
                <div class="audit-meta-item">
                  <span>更新时间</span>
                  <strong>{{ formatDateTime(selectedDetail.item.updated_at) }}</strong>
                </div>
                <div class="audit-meta-item">
                  <span>自动置信度</span>
                  <strong>{{ formatConfidence(selectedDetail.item.auto_confidence) }}</strong>
                </div>
                <div class="audit-meta-item">
                  <span>人工结论</span>
                  <strong>{{ getManualVerdictDisplay(selectedDetail.item) }}</strong>
                </div>
                <div class="audit-meta-item">
                  <span>复查人</span>
                  <strong>{{ selectedDetail.item.reviewer || '未指定' }}</strong>
                </div>
              </div>
            </div>
          </section>

          <section class="audit-card audit-card--actions">
            <div class="audit-card__title">案件操作</div>
            <div class="audit-sidebar__actions">
              <el-button @click="openReportPreview()">报告预览</el-button>
              <el-button type="primary" plain :loading="exporting" @click="downloadReport">导出报告</el-button>
              <el-button type="danger" plain :loading="deletingId === selectedDetail.item.id" @click="handleDelete(selectedDetail.item)">
                删除记录
              </el-button>
            </div>
          </section>
        </aside>

        <section class="audit-main">
          <section class="audit-card audit-card--summary">
            <div class="audit-section-head">
              <div>
                <div class="audit-card__eyebrow">智能体概览</div>
                <div class="audit-card__title">四智能体审核链路</div>
              </div>
              <div class="audit-section-head__hint">点击卡片可切换详细判定面板</div>
            </div>

            <div class="audit-summary-grid">
              <button
                v-for="panel in agentPanels"
                :key="panel.key"
                type="button"
                class="audit-summary-card"
                :class="{ 'is-active': activeAgentTab === panel.key }"
                @click="activeAgentTab = panel.key"
              >
                <span>{{ panel.shortTitle }}</span>
                <strong>{{ panel.verdict || '待定' }}</strong>
                <div class="audit-summary-card__meta">{{ formatConfidence(panel.confidence) }}</div>
                <p>{{ panel.summary }}</p>
              </button>
            </div>
          </section>

          <section class="audit-card audit-card--detail">
            <div class="audit-section-head">
              <div>
                <div class="audit-card__eyebrow">证据面板</div>
                <div class="audit-card__title">{{ activeAgentPanel?.title || '智能体详情' }}</div>
              </div>
              <el-tag size="small" effect="dark" :type="activeAgentPanel?.key === 'judge' ? 'primary' : 'info'">
                {{ activeAgentPanel?.verdict || '待定' }} / {{ formatConfidence(activeAgentPanel?.confidence || 0) }}
              </el-tag>
            </div>

            <div v-if="activeAgentPanel" class="review-agent-panel review-agent-panel--active">
              <div class="review-agent-panel__head review-agent-panel__head--stacked">
                <div>
                  <h4>{{ activeAgentPanel.title }}</h4>
                  <p>{{ activeAgentPanel.subtitle }}</p>
                </div>
              </div>

              <div class="review-agent-panel__section">
                <div class="review-agent-panel__label">摘要</div>
                <p>{{ activeAgentPanel.summary }}</p>
              </div>

              <div v-if="activeAgentPanel.logs?.length" class="review-agent-panel__section">
                <div class="review-agent-panel__label">执行日志</div>
                <ul class="review-agent-panel__list">
                  <li v-for="(log, logIndex) in activeAgentPanel.logs" :key="`${activeAgentPanel.key}-log-${logIndex}`">
                    {{ log }}
                  </li>
                </ul>
              </div>

              <div v-if="activeAgentPanel.sections?.length" class="review-agent-panel__section">
                <div class="review-agent-panel__label">详细判定</div>
                <div
                  v-for="(section, sectionIndex) in activeAgentPanel.sections"
                  :key="`${activeAgentPanel.key}-section-${sectionIndex}`"
                  class="review-agent-panel__block"
                >
                  <strong>{{ section.title }}</strong>
                  <p>{{ section.content || '暂无内容。' }}</p>
                </div>
              </div>

              <div v-else-if="activeAgentPanel.rawOutput" class="review-agent-panel__section">
                <div class="review-agent-panel__label">原始输出</div>
                <div class="review-agent-panel__block">
                  <p>{{ activeAgentPanel.rawOutput }}</p>
                </div>
              </div>
            </div>
          </section>

          <section class="audit-card audit-card--form">
            <div class="audit-section-head">
              <div>
                <div class="audit-card__eyebrow">人工复核</div>
                <div class="audit-card__title">复查结论填写区</div>
              </div>
            </div>

            <el-form label-position="top" class="review-form review-form--workspace">
              <div class="review-form__grid">
                <el-form-item label="复查状态">
                  <el-select v-model="reviewForm.review_status">
                    <el-option
                      v-for="item in reviewStatusOptions"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="人工结论">
                  <el-select v-model="reviewForm.manual_verdict">
                    <el-option
                      v-for="item in manualVerdictOptions"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="复查人">
                  <el-input v-model="reviewForm.reviewer" placeholder="请输入复查人姓名或角色" />
                </el-form-item>
              </div>

              <el-form-item label="复查备注">
                <el-input
                  v-model="reviewForm.notes"
                  type="textarea"
                  :rows="6"
                  resize="none"
                  placeholder="记录人工复查依据、外部证据来源或后续跟进建议。"
                />
              </el-form-item>
            </el-form>

            <div class="review-dialog__footer review-dialog__footer--between">
              <div class="review-dialog__footer-actions"></div>
              <div class="review-dialog__footer-actions">
                <el-button @click="dialogVisible = false">关闭</el-button>
                <el-button type="primary" :loading="submitting" @click="submitReview">保存复查结果</el-button>
              </div>
            </div>
          </section>
        </section>
      </div>
    </el-dialog>

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
            <div class="report-preview-dialog__eyebrow">检测报告预览</div>
            <div class="report-preview-dialog__title">{{ selectedDetail?.item?.title || '未命名检测任务' }}</div>
          </div>
          <el-button type="primary" :disabled="exporting || !selectedReportSnapshot" @click="downloadReport">
            {{ exporting ? '导出中...' : '下载 PDF 报告' }}
          </el-button>
        </div>
      </template>

      <div class="report-preview-dialog__body">
        <ReportDocument :report="selectedReportSnapshot" />
      </div>
    </el-dialog>

    <div class="pdf-report-stage" aria-hidden="true">
      <ReportDocument ref="reportExportRef" :report="selectedReportSnapshot" />
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import AppNavbar from '../components/AppNavbar.vue'
import ReportDocument from '../components/ReportDocument.vue'
import {
  deleteHistoryRecord,
  getHistoryDetail,
  getHistoryRecords,
  getHistorySummary,
  updateHistoryReview
} from '../api'
import { createReportSnapshot, exportReportPdf } from '../utils/reportExport'
import {
  AUTO_MANUAL_VERDICT,
  formatConfidence,
  formatDateTime,
  getBinaryLabel,
  getBinaryTagType,
  getFakeTypeColor,
  getFakeTypeLabel,
  getReviewStatusLabel,
  getReviewStatusType,
  manualVerdictOptions,
  reviewStatusOptions
} from '../utils/contentLabels'

const DETECTION_HISTORY_STORAGE_KEY = 'mac_judge_latest_history_id'
const DETECTION_STATE_STORAGE_KEY = 'mac_judge_latest_detection_state'
const REPORT_STORAGE_KEY = 'rumor_detection_latest_report'
const EMPTY_REPORT_SNAPSHOT = Object.freeze({
  generatedAt: '',
  title: '',
  meta: {},
  judge: { logs: [] },
  verdict: {},
  evidenceAgents: []
})

const loading = ref(false)
const dialogVisible = ref(false)
const reportDialogVisible = ref(false)
const submitting = ref(false)
const exporting = ref(false)
const deletingId = ref('')
const selectedDetail = ref(null)
const reportExportRef = ref(null)
const records = ref([])
const activeAgentTab = ref('judge')
const summary = reactive({
  total: 0,
  pending_review: 0,
  approved_count: 0,
  corrected_count: 0,
  flagged_count: 0
})

const pagination = reactive({
  page: 1,
  pageSize: 8,
  total: 0
})

const filters = reactive({
  review_status: '',
  search: ''
})

const reviewForm = reactive({
  review_status: 'approved',
  manual_verdict: AUTO_MANUAL_VERDICT,
  reviewer: '',
  notes: ''
})

let searchTimeout = null

function sanitizeJudgeLogs(logs = []) {
  return [...(logs || [])].filter((log) => {
    const normalized = String(log || '').trim()
    return !normalized.startsWith('裁决耗时：') && !normalized.startsWith('端到端总耗时：')
  })
}

function createAgentPanel(key, title, subtitle, agent = {}) {
  const shortTitleMap = {
    text_analysis: '文本审核',
    visual_investigate: '视觉审核',
    consistency_check: '一致性审核',
    judge: '综合裁决'
  }

  return {
    key,
    shortTitle: shortTitleMap[key] || title,
    title,
    subtitle,
    status: agent?.status || 'done',
    verdict: agent?.verdict || '待定',
    confidence: agent?.confidence || 0,
    summary: agent?.summary || agent?.excerpt || '暂无摘要。',
    excerpt: agent?.excerpt || agent?.summary || '',
    sections: [...(agent?.report_sections || agent?.reportSections || [])],
    reportSections: [...(agent?.report_sections || agent?.reportSections || [])],
    logs: [...(agent?.logs || [])],
    rawOutput: agent?.raw_output || ''
  }
}

const agentPanels = computed(() => {
  if (!selectedDetail.value) return []

  const detail = selectedDetail.value
  return [
    createAgentPanel(
      'text_analysis',
      '文本真实性分析智能体',
      '抽取实体执行外部搜索，核验文本事实',
      detail.agents?.text_analysis
    ),
    createAgentPanel(
      'visual_investigate',
      '视觉真实性检测智能体',
      '分析图像语义与事实线索',
      detail.agents?.visual_investigate
    ),
    createAgentPanel(
      'consistency_check',
      '跨模态一致性智能体',
      '判断图文语义是否一致',
      detail.agents?.consistency_check
    ),
    {
      key: 'judge',
      shortTitle: '综合裁决',
      title: '综合裁决智能体',
      subtitle: '融合三路证据并输出最终结论',
      verdict: getBinaryLabel(detail.item?.auto_verdict),
      confidence: detail.item?.auto_confidence || 0,
      summary: detail.item?.auto_reasoning || '暂无综合裁决说明。',
      sections: detail.judge?.raw_output
        ? [{ title: '综合裁决原始输出', content: detail.judge.raw_output }]
        : [],
      logs: sanitizeJudgeLogs(detail.judge?.logs || []),
      rawOutput: detail.judge?.raw_output || ''
    }
  ]
})

const activeAgentPanel = computed(() => {
  return agentPanels.value.find((panel) => panel.key === activeAgentTab.value) || agentPanels.value[0] || null
})

const selectedReportSnapshot = computed(() => {
  if (!selectedDetail.value) return EMPTY_REPORT_SNAPSHOT

  const detail = selectedDetail.value
  return createReportSnapshot({
    title: detail.item?.title || '',
    meta: detail.meta || {},
    judge: {
      title: '综合裁决智能体',
      subtitle: '融合三路证据并输出最终结论',
      status: detail.judge?.status || 'done',
      logs: sanitizeJudgeLogs(detail.judge?.logs || [])
    },
    verdict: {
      verdict: getBinaryLabel(detail.item?.auto_verdict),
      category: getFakeTypeLabel(detail.item?.auto_category),
      confidence: detail.item?.auto_confidence || 0,
      reasoning: detail.item?.auto_reasoning || ''
    },
    evidenceAgents: [
      createAgentPanel(
        'text',
        '文本真实性分析智能体',
        '抽取实体执行外部搜索，核验文本事实',
        detail.agents?.text_analysis
      ),
      createAgentPanel(
        'visual',
        '视觉真实性检测智能体',
        '分析图像语义与事实线索',
        detail.agents?.visual_investigate
      ),
      createAgentPanel(
        'consistency',
        '跨模态一致性智能体',
        '判断图文语义是否一致',
        detail.agents?.consistency_check
      )
    ]
  })
})

function clearDetectionRestoreCache(recordId) {
  if (sessionStorage.getItem(DETECTION_HISTORY_STORAGE_KEY) !== recordId) {
    return
  }

  sessionStorage.removeItem(DETECTION_HISTORY_STORAGE_KEY)
  sessionStorage.removeItem(DETECTION_STATE_STORAGE_KEY)
  sessionStorage.removeItem(REPORT_STORAGE_KEY)
}

function hasReviewRecord(item = {}) {
  return Boolean(
    item?.reviewed_at ||
    item?.reviewer ||
    item?.review_notes ||
    (item?.review_status && item.review_status !== 'pending')
  )
}

function resolveManualVerdictValue(item = {}) {
  if (item?.manual_verdict) {
    return item.manual_verdict
  }

  return hasReviewRecord(item) ? AUTO_MANUAL_VERDICT : ''
}

function getManualVerdictDisplay(item = {}) {
  const manualVerdict = resolveManualVerdictValue(item)

  if (manualVerdict === AUTO_MANUAL_VERDICT) {
    const autoVerdict = getBinaryLabel(item?.auto_verdict)
    return autoVerdict && autoVerdict !== '未知' ? `沿用自动结论（${autoVerdict}）` : '沿用自动结论'
  }

  if (manualVerdict) {
    return getBinaryLabel(manualVerdict)
  }

  return '未填写'
}

function syncReviewForm(detail) {
  reviewForm.review_status = detail?.item?.review_status || 'approved'
  reviewForm.manual_verdict = resolveManualVerdictValue(detail?.item)
  reviewForm.reviewer = detail?.item?.reviewer || ''
  reviewForm.notes = detail?.item?.review_notes || ''
}

async function fetchSummary() {
  Object.assign(summary, await getHistorySummary())
}

async function fetchRecords() {
  loading.value = true
  try {
    const response = await getHistoryRecords({
      page: pagination.page,
      page_size: pagination.pageSize,
      review_status: filters.review_status || undefined,
      search: filters.search || undefined
    })
    records.value = response?.items || []
    pagination.total = response?.total || 0
  } catch (error) {
    console.error('Failed to fetch history records:', error)
  } finally {
    loading.value = false
  }
}

async function reloadAll() {
  await Promise.all([fetchSummary(), fetchRecords()])
}

function handleFilter() {
  pagination.page = 1
  fetchRecords()
}

function handleSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    pagination.page = 1
    fetchRecords()
  }, 300)
}

function handlePageChange() {
  fetchRecords()
}

function handleSizeChange() {
  pagination.page = 1
  fetchRecords()
}

async function loadDetailById(recordId) {
  const detail = await getHistoryDetail(recordId)
  selectedDetail.value = detail
  syncReviewForm(detail)
  activeAgentTab.value = 'judge'
  return detail
}

async function openReview(item) {
  try {
    await loadDetailById(item.id)
    dialogVisible.value = true
  } catch (error) {
    console.error('Failed to open review detail:', error)
    ElMessage.error('读取复查详情失败，请稍后重试')
  }
}

async function openReportPreview(item = null) {
  try {
    if (item?.id) {
      await loadDetailById(item.id)
    } else if (!selectedDetail.value?.item?.id) {
      return
    }

    reportDialogVisible.value = true
  } catch (error) {
    console.error('Failed to open report preview:', error)
    ElMessage.error('读取报告失败，请稍后重试')
  }
}

async function submitReview() {
  if (!selectedDetail.value?.item?.id) return

  submitting.value = true
  try {
    const response = await updateHistoryReview(selectedDetail.value.item.id, {
      review_status: reviewForm.review_status,
      manual_verdict: reviewForm.manual_verdict === AUTO_MANUAL_VERDICT ? '' : reviewForm.manual_verdict,
      reviewer: reviewForm.reviewer,
      notes: reviewForm.notes
    })

    selectedDetail.value.item = response.item
    await reloadAll()
    ElMessage.success('人工复查结果已保存')
    dialogVisible.value = false
  } catch (error) {
    console.error('Failed to save review:', error)
    ElMessage.error('保存复查结果失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(item) {
  const recordId = item?.id || selectedDetail.value?.item?.id
  const recordTitle = item?.title || selectedDetail.value?.item?.title || '当前记录'
  if (!recordId) return

  try {
    await ElMessageBox.confirm(
      `确定删除“${recordTitle}”吗？删除后归档记录与上传图片将一并移除。`,
      '删除历史记录',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }

  deletingId.value = recordId
  try {
    await deleteHistoryRecord(recordId)
    clearDetectionRestoreCache(recordId)

    if (records.value.length === 1 && pagination.page > 1) {
      pagination.page -= 1
    }

    if (selectedDetail.value?.item?.id === recordId) {
      dialogVisible.value = false
      reportDialogVisible.value = false
      selectedDetail.value = null
    }

    await reloadAll()
    ElMessage.success('历史记录已删除')
  } catch (error) {
    console.error('Failed to delete history record:', error)
    ElMessage.error('删除历史记录失败，请稍后重试')
  } finally {
    deletingId.value = ''
  }
}

async function downloadReport() {
  if (!selectedReportSnapshot.value || exporting.value) return

  const element = reportExportRef.value?.$el || reportExportRef.value
  if (!element) {
    ElMessage.error('PDF 报告容器未准备好')
    return
  }

  exporting.value = true
  try {
    await nextTick()
    await exportReportPdf(element, selectedDetail.value?.item?.title || 'history_report')
    ElMessage.success('PDF 检测报告已开始下载')
  } catch (error) {
    console.error('Failed to export PDF report:', error)
    ElMessage.error('PDF 导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  reloadAll()
})
</script>
