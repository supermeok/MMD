<template>
  <div class="page detect-page portal-page">
    <div class="portal-shell">
      <AppNavbar />

      <section class="page-intro">
        <div>
          <div class="page-intro__eyebrow">System Manual</div>
          <h1>系统手册</h1>
        </div>
        <div class="page-intro__hint">
          最近更新：{{ manual.updated_at ? formatDateTime(manual.updated_at) : '首次初始化后自动生成' }}
        </div>
      </section>

      <div class="manual-grid">
        <article v-for="section in visibleSections" :key="section.id" class="manual-card">
          <div class="manual-card__header">
            <span class="manual-card__eyebrow">{{ section.id }}</span>
            <h3>{{ section.title }}</h3>
            <p>{{ section.summary }}</p>
          </div>

          <div class="manual-card__block">
            <h4>操作要点</h4>
            <ul>
              <li v-for="item in section.bullets" :key="item">{{ item }}</li>
            </ul>
          </div>

          <div class="manual-card__block manual-card__block--highlight">
            <h4>实践建议</h4>
            <ul>
              <li v-for="item in section.highlights" :key="item">{{ item }}</li>
            </ul>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive } from 'vue'

import AppNavbar from '../components/AppNavbar.vue'
import { getSystemManual } from '../api'
import { formatDateTime } from '../utils/contentLabels'

const manual = reactive({
  updated_at: '',
  sections: []
})

const visibleSections = computed(() => manual.sections.filter((section) => section.id !== 'operations'))

async function loadManual() {
  try {
    const response = await getSystemManual()
    manual.updated_at = response?.updated_at || ''
    manual.sections = response?.sections || []
  } catch (error) {
    console.error('Failed to fetch manual:', error)
  }
}

onMounted(() => {
  loadManual()
})
</script>
