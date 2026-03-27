<template>
  <div class="pdf-report">
    <div class="pdf-report__header">
      <div class="pdf-report__eyebrow">Rumor Detection Report</div>
      <h1>完整检测报告</h1>
      <div class="pdf-report__meta-grid">
        <div class="pdf-report__meta-item">
          <span>生成时间</span>
          <strong>{{ report.generatedAt || '--' }}</strong>
        </div>
        <div class="pdf-report__meta-item">
          <span>检测模型</span>
          <strong>{{ report.meta?.model || '--' }}</strong>
        </div>
        <div class="pdf-report__meta-item">
          <span>上传图片</span>
          <strong>{{ report.meta?.filename || '--' }}</strong>
        </div>
        <div class="pdf-report__meta-item">
          <span>总耗时</span>
          <strong>{{ report.meta?.elapsed_ms ? `${report.meta.elapsed_ms} ms` : '--' }}</strong>
        </div>
      </div>
    </div>

    <div class="pdf-report__section">
      <div class="pdf-report__section-title">新闻输入</div>
      <div class="pdf-report__block">
        <div class="pdf-report__label">新闻标题</div>
        <div class="pdf-report__text">
          <p class="pdf-report__paragraph">{{ report.title || '未填写' }}</p>
        </div>
      </div>
    </div>

    <div class="pdf-report__section">
      <div class="pdf-report__section-title">最终裁决</div>
      <div class="pdf-report__summary-grid">
        <div class="pdf-report__summary-card">
          <span>判定</span>
          <strong>{{ report.verdict?.verdict || '--' }}</strong>
        </div>
        <div class="pdf-report__summary-card">
          <span>类别</span>
          <strong>{{ report.verdict?.category || '--' }}</strong>
        </div>
        <div class="pdf-report__summary-card">
          <span>置信度</span>
          <strong>{{ report.verdict?.confidence ?? 0 }}%</strong>
        </div>
      </div>
      <div class="pdf-report__block">
        <div class="pdf-report__label">裁决理由</div>
        <div class="pdf-report__text">
          <p
            v-for="(paragraph, index) in formatPdfParagraphs(report.verdict?.reasoning || '--')"
            :key="`reason-${index}`"
            class="pdf-report__paragraph"
          >
            {{ paragraph }}
          </p>
        </div>
      </div>
      <div class="pdf-report__block">
        <div class="pdf-report__label">综合裁决过程</div>
        <ol class="pdf-report__list">
          <li v-for="(log, idx) in report.judge?.logs || []" :key="`judge-${idx}`">{{ log }}</li>
        </ol>
      </div>
    </div>

    <div
      v-for="(agent, index) in report.evidenceAgents || []"
      :key="agent.key || index"
      class="pdf-report__section pdf-report__agent"
      :class="{ 'pdf-page-break-before': index > 0 }"
    >
      <div class="pdf-report__section-title">证据智能体 {{ index + 1 }}：{{ agent.title }}</div>

      <div class="pdf-report__summary-grid">
        <div class="pdf-report__summary-card">
          <span>判定结果</span>
          <strong>{{ agent.verdict || '--' }}</strong>
        </div>
        <div class="pdf-report__summary-card">
          <span>置信度</span>
          <strong>{{ agent.confidence ?? 0 }}%</strong>
        </div>
      </div>

      <div class="pdf-report__block">
        <div class="pdf-report__label">模型摘录</div>
        <div class="pdf-report__text">
          <p
            v-for="(paragraph, excerptIndex) in formatPdfParagraphs(agent.excerpt || '--')"
            :key="`${agent.key || index}-excerpt-${excerptIndex}`"
            class="pdf-report__paragraph"
          >
            {{ paragraph }}
          </p>
        </div>
      </div>

      <div class="pdf-report__block">
        <div class="pdf-report__label">详细判定流程</div>
        <div
          v-for="(section, sectionIndex) in agent.reportSections || []"
          :key="`${agent.key || index}-${sectionIndex}`"
          class="pdf-report__detail"
        >
          <div class="pdf-report__detail-title">{{ sectionIndex + 1 }}. {{ section.title }}</div>
          <div class="pdf-report__text">
            <p
              v-for="(paragraph, paragraphIndex) in formatPdfParagraphs(section.content || '--')"
              :key="`${agent.key || index}-${sectionIndex}-${paragraphIndex}`"
              class="pdf-report__paragraph"
            >
              {{ paragraph }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatPdfParagraphs } from '../utils/reportExport'

defineProps({
  report: {
    type: Object,
    default: () => ({
      generatedAt: '',
      title: '',
      meta: {},
      judge: { logs: [] },
      verdict: {},
      evidenceAgents: []
    })
  }
})
</script>
