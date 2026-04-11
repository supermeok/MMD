<template>
  <div class="page detect-page portal-page">
    <div class="portal-shell">
      <AppNavbar />

      <section class="page-intro">
        <div>
          <div class="page-intro__eyebrow">Knowledge Base</div>
          <h1>图文对新闻知识库</h1>
        </div>
        <div class="page-intro__actions">
          <el-switch
            v-model="isChinese"
            active-text="中文"
            inactive-text="English"
            @change="handleLangChange"
          />
        </div>
      </section>

      <div class="portal-filter-bar portal-filter-bar--knowledge">
        <el-select v-model="filters.fake_type" clearable :placeholder="isChinese ? '选择失真类型' : 'Select Category'" @change="handleFilter">
          <el-option :label="isChinese ? '全部类型' : 'All Types'" value="" />
          <el-option :label="isChinese ? '真实新闻' : 'Original'" value="original" />
          <el-option :label="isChinese ? '文本虚假' : 'Textual Distortion'" value="textual_veracity_distortion" />
          <el-option :label="isChinese ? '视觉虚假' : 'Visual Distortion'" value="visual_veracity_distortion" />
          <el-option :label="isChinese ? '图文不一致' : 'Mismatch'" value="mismatch" />
        </el-select>

        <el-select v-model="filters.binary_fake_type" clearable :placeholder="isChinese ? '选择真假分类' : 'Select Label'" @change="handleFilter">
          <el-option :label="isChinese ? '全部分类' : 'All Labels'" value="" />
          <el-option :label="isChinese ? '真实' : 'True'" :value="isChinese ? '真实' : 'True'" />
          <el-option :label="isChinese ? '虚假' : 'Fake'" :value="isChinese ? '虚假' : 'Fake'" />
        </el-select>

        <el-select v-model="filters.theme" clearable :placeholder="isChinese ? '选择主题' : 'Select Theme'" @change="handleFilter">
          <el-option :label="isChinese ? '全部主题' : 'All Themes'" value="" />
          <el-option
            v-for="item in knowledgeThemeOptions"
            :key="item.value"
            :label="isChinese ? item.labelZh : item.labelEn"
            :value="item.value"
          />
        </el-select>

        <el-input
          v-model="filters.search"
          clearable
          :placeholder="isChinese ? '搜索新闻标题...' : 'Search titles...'"
          @input="handleSearch"
        />
      </div>

      <div v-loading="loading" class="knowledge-card-grid">
        <article v-for="item in newsItems" :key="item.id" class="knowledge-card">
          <div class="knowledge-card__image-wrap">
            <img :src="item.image_url" :alt="item.title" class="knowledge-card__image" />
          </div>

          <div class="knowledge-card__body">
            <div class="knowledge-card__tags">
              <el-tag size="small" :type="getBinaryTagType(item.binary_fake_type)">
                {{ getBinaryLabel(item.binary_fake_type) }}
              </el-tag>
              <el-tag size="small" :type="getFakeTypeColor(item.fake_type)">
                {{ getFakeTypeLabel(item.fake_type) }}
              </el-tag>
              <el-tag size="small" :type="getKnowledgeThemeType(item.theme)">
                {{ getKnowledgeThemeLabel(item.theme, isChinese) }}
              </el-tag>
            </div>

            <h3>{{ item.title }}</h3>
            <p>{{ item.reasoning || (isChinese ? '暂无推理摘要。' : 'No reasoning available.') }}</p>

            <div class="knowledge-card__footer">
              <el-button text class="portal-link-btn" @click="openDetail(item)">
                {{ isChinese ? '查看分析' : 'View Analysis' }}
              </el-button>
            </div>
          </div>
        </article>

        <div v-if="!loading && !newsItems.length" class="portal-empty-state">
          暂无匹配的知识库样本。
        </div>
      </div>

      <div class="portal-pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[12, 24, 36, 48]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" width="720px" :title="isChinese ? '样本分析详情' : 'Analysis Details'">
      <div v-if="selectedItem" class="knowledge-detail">
        <div class="knowledge-detail__image-wrap">
          <img :src="selectedItem.image_url" :alt="selectedItem.title" class="knowledge-detail__image" />
        </div>
        <div class="knowledge-detail__content">
          <div class="knowledge-card__tags">
            <el-tag size="small" :type="getBinaryTagType(selectedItem.binary_fake_type)">
              {{ getBinaryLabel(selectedItem.binary_fake_type) }}
            </el-tag>
            <el-tag size="small" :type="getFakeTypeColor(selectedItem.fake_type)">
              {{ getFakeTypeLabel(selectedItem.fake_type) }}
            </el-tag>
            <el-tag size="small" :type="getKnowledgeThemeType(selectedItem.theme)">
              {{ getKnowledgeThemeLabel(selectedItem.theme, isChinese) }}
            </el-tag>
          </div>
          <h3>{{ selectedItem.title }}</h3>
          <p>{{ selectedItem.reasoning || '暂无分析说明。' }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import AppNavbar from '../components/AppNavbar.vue'
import { getKnowledgeArticles } from '../api'
import {
  getBinaryLabel,
  getBinaryTagType,
  getFakeTypeColor,
  getFakeTypeLabel,
  getKnowledgeThemeLabel,
  getKnowledgeThemeType,
  knowledgeThemeOptions
} from '../utils/contentLabels'

const loading = ref(false)
const dialogVisible = ref(false)
const selectedItem = ref(null)
const newsItems = ref([])
const isChinese = ref(true)

const pagination = reactive({
  page: 1,
  pageSize: 12,
  total: 0
})

const filters = reactive({
  fake_type: '',
  binary_fake_type: '',
  theme: '',
  search: ''
})

let searchTimeout = null

async function fetchNews() {
  loading.value = true
  try {
    const response = await getKnowledgeArticles({
      page: pagination.page,
      page_size: pagination.pageSize,
      lang: isChinese.value ? 'zh' : 'en',
      fake_type: filters.fake_type || undefined,
      binary_fake_type: filters.binary_fake_type || undefined,
      theme: filters.theme || undefined,
      search: filters.search || undefined
    })

    newsItems.value = response?.items || []
    pagination.total = response?.total || 0
  } catch (error) {
    console.error('Failed to fetch knowledge base:', error)
  } finally {
    loading.value = false
  }
}

async function reloadAll() {
  await fetchNews()
}

function handleLangChange() {
  pagination.page = 1
  filters.fake_type = ''
  filters.binary_fake_type = ''
  filters.theme = ''
  filters.search = ''
  reloadAll()
}

function handleFilter() {
  pagination.page = 1
  fetchNews()
}

function handleSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    pagination.page = 1
    fetchNews()
  }, 300)
}

function handlePageChange() {
  fetchNews()
}

function handleSizeChange() {
  pagination.page = 1
  fetchNews()
}

function openDetail(item) {
  selectedItem.value = item
  dialogVisible.value = true
}

onMounted(() => {
  reloadAll()
})
</script>
