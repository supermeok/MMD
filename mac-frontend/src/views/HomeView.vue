<template>
  <div class="home-page portal-page">
    <div class="bg-grid"></div>
    <div class="cyber-grid"></div>

    <div class="home-container portal-shell">
      <AppNavbar />

      <section class="portal-hero">
        <div class="portal-hero__main portal-hero__main--card animate-slide-left">
          <div class="portal-hero__main-copy">
            <h1 class="tech-gradient-text">多智裁决</h1>
            <p class="portal-hero__desc">基于多智能体裁决的谣言检测系统</p>
          </div>

          <div class="portal-hero__main-panel">
            <div class="portal-hero__actions portal-hero__actions--home">
              <el-button type="primary" size="large" class="start-btn portal-hero__button neon-button" @click="goTo('/detect')">
                开始检测
              </el-button>
              <el-button size="large" class="home-ghost-btn portal-hero__button neon-button" @click="goTo('/knowledge')">
                进入知识库
              </el-button>
            </div>

            <div class="portal-hero__metrics">
              <div class="portal-hero__metric-card hover-lift">
                <span>历史记录</span>
                <strong>{{ overview.historyTotal }}</strong>
              </div>
              <div class="portal-hero__metric-card portal-hero__metric-card--emphasis hover-lift animate-glow">
                <span>待人工复查</span>
                <strong>{{ overview.pendingReview }}</strong>
              </div>
            </div>
          </div>
        </div>

        <div class="portal-hero__side animate-slide-right">
          <el-card shadow="never" class="flow-card hero-card tech-card">
            <template #header>
              <div class="flow-card-header">
                <span>系统核心流程</span>
                <span class="flow-card-subtitle">多智裁决</span>
              </div>
            </template>

            <div class="flow-top">
              <div class="flow-agent hover-lift stagger-1">
                <div class="flow-agent-icon">
                  <img :src="textIcon" alt="文本真实性" />
                </div>
                <div class="flow-agent-title">文本真实性分析</div>
              </div>

              <div class="flow-agent hover-lift stagger-2">
                <div class="flow-agent-icon">
                  <img :src="visualIcon" alt="视觉真实性" />
                </div>
                <div class="flow-agent-title">视觉真实性检测</div>
              </div>

              <div class="flow-agent hover-lift stagger-3">
                <div class="flow-agent-icon">
                  <img :src="consistencyIcon" alt="跨模态一致性" />
                </div>
                <div class="flow-agent-title">跨模态一致性判断</div>
              </div>
            </div>

            <div class="flow-merge">
              <div class="flow-merge__line"></div>
              <div class="flow-merge__arrow"></div>
            </div>

            <div class="flow-judge animate-float">
              <div class="judge-robot">
                <img :src="judgeIcon" alt="综合裁决智能体" />
              </div>
              <div class="judge-title">综合裁决智能体</div>
              <div class="judge-desc">输出最终检测结果</div>
            </div>
          </el-card>
        </div>
      </section>

      <section class="portal-section animate-slide-up">
        <div class="portal-section__header">
          <div>
            <div class="portal-section__eyebrow">功能入口</div>
            <h2>系统模块</h2>
          </div>
        </div>

        <div class="portal-feature-grid">
          <article v-for="(item, index) in features" :key="item.path" class="portal-feature-card hover-lift tech-card" :class="'stagger-' + (index + 1)">
            <div class="portal-feature-card__head">
              <span class="portal-feature-card__tag">{{ item.tag }}</span>
              <el-button text class="portal-link-btn" @click="goTo(item.path)">进入</el-button>
            </div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </article>
        </div>
      </section>

      <section class="portal-section animate-slide-up">
        <div class="portal-section__header">
          <div>
            <div class="portal-section__eyebrow">样本预览</div>
            <h2>部分样本</h2>
          </div>
          <div class="portal-section__actions">
            <el-button
              circle
              class="portal-icon-btn portal-icon-btn--refresh"
              :loading="previewLoading"
              :icon="RefreshRight"
              aria-label="刷新样本"
              title="刷新样本"
              @click="refreshHomeData"
            />
            <el-button class="home-ghost-btn home-ghost-btn--small neon-button" @click="goTo('/knowledge')">
              进入知识库
            </el-button>
          </div>
        </div>

        <div v-loading="previewLoading && !previewItems.length">
          <transition-group name="sample-swap" tag="div" class="portal-preview-grid">
            <article
              v-for="(item, index) in previewItems"
              :key="`${item.id}-${previewVersion}`"
              class="knowledge-preview-card hover-lift tech-card"
              :class="getPreviewStaggerClass(index)"
            >
              <div class="knowledge-preview-card__image-wrap">
                <img :src="item.image_url" :alt="item.title" class="knowledge-preview-card__image" />
              </div>
              <div class="knowledge-preview-card__body">
                <div class="knowledge-preview-card__tags">
                  <el-tag size="small" :type="getBinaryTagType(item.binary_fake_type)">
                    {{ getBinaryLabel(item.binary_fake_type) }}
                  </el-tag>
                  <el-tag size="small" :type="getFakeTypeColor(item.fake_type)">
                    {{ getFakeTypeLabel(item.fake_type) }}
                  </el-tag>
                </div>
                <h3>{{ item.title }}</h3>
                <p>{{ item.reasoning || '暂无推理摘要。' }}</p>
              </div>
            </article>

            <div v-if="!previewLoading && !previewItems.length" key="empty" class="portal-empty-state">
              暂无样本数据。
            </div>
          </transition-group>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { RefreshRight } from '@element-plus/icons-vue'
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import AppNavbar from '../components/AppNavbar.vue'
import { getHistorySummary, getKnowledgeArticles } from '../api'
import {
  getBinaryLabel,
  getBinaryTagType,
  getFakeTypeColor,
  getFakeTypeLabel
} from '../utils/contentLabels'

const router = useRouter()
const previewLoading = ref(false)
const previewItems = ref([])
const previewVersion = ref(0)
const overview = reactive({
  historyTotal: 0,
  pendingReview: 0
})

const textIcon = new URL('../assets/text-agent.svg', import.meta.url).href
const visualIcon = new URL('../assets/visual-agent.svg', import.meta.url).href
const consistencyIcon = new URL('../assets/consistency-agent.svg', import.meta.url).href
const judgeIcon = new URL('../assets/judge-agent.svg', import.meta.url).href

const features = [
  {
    tag: 'Analytics',
    title: '数据看板',
    description: '查看数据分布、主题细分与复查统计。',
    path: '/analytics'
  },
  {
    tag: 'History',
    title: '历史检测记录',
    description: '查看历史检测结果并执行人工复查。',
    path: '/history'
  },
  {
    tag: 'Manual',
    title: '系统手册',
    description: '查看系统使用说明和操作规范。',
    path: '/manual'
  }
]

function goTo(path) {
  router.push(path)
}

async function loadHomeData() {
  if (previewLoading.value) {
    return
  }

  previewLoading.value = true

  try {
    const [historySummary, knowledgePreview] = await Promise.all([
      getHistorySummary(),
      getKnowledgeArticles({ page: 1, page_size: 6, lang: 'zh', random_sample: true })
    ])

    overview.historyTotal = historySummary?.total || 0
    overview.pendingReview = historySummary?.pending_review || 0
    previewItems.value = knowledgePreview?.items || []
    previewVersion.value += 1
  } catch (error) {
    console.error('Failed to load home overview:', error)
  } finally {
    previewLoading.value = false
  }
}

function refreshHomeData() {
  loadHomeData()
}

function getPreviewStaggerClass(index) {
  return `stagger-${(index % 3) + 1}`
}

onMounted(() => {
  loadHomeData()
})
</script>
