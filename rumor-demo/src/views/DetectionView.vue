<template>
  <div class="page">
    <div class="detect-topbar">
      <router-link to="/" class="back-link">← 返回首页</router-link>
      <div class="topbar-title">检测分析页</div>
    </div>

    <div class="hero">
      <div>
        <div class="eyebrow">Detection Workspace</div>
        <h1>多智能体谣言检测演示平台</h1>
        <p>上传新闻标题和图片后，三个证据收集智能体并行分析，随后由综合裁决智能体给出最终结论。</p>
      </div>
    </div>

    <div class="control-panel">
      <div class="control-card">
        <div class="control-title">新闻输入</div>

        <label class="field-label">新闻标题</label>
        <textarea
          v-model="title"
          class="text-input"
          rows="4"
          placeholder="请输入新闻标题，例如：某地突发重大事件，现场图片曝光..."
        />

        <label class="field-label">新闻图片</label>
        <div class="upload-row">
          <label class="upload-box">
            <input type="file" accept="image/*" @change="handleFileChange" />
            <span>{{ imagePreview ? '重新选择图片' : '点击上传图片' }}</span>
          </label>

          <div v-if="imagePreview" class="image-preview-wrap">
            <img :src="imagePreview" alt="preview" class="image-preview" />
          </div>
        </div>

        <div class="actions">
          <button class="primary-btn" :disabled="!canStart || running" @click="startDemo">
            {{ running ? '分析进行中...' : '开始分析检测' }}
          </button>
          <button class="ghost-btn" :disabled="running" @click="resetAll">重置</button>
        </div>
      </div>
    </div>

    <div class="agents-top">
      <AgentCard
        v-for="agent in evidenceAgents"
        :key="agent.key"
        :title="agent.title"
        :subtitle="agent.subtitle"
        :icon="agent.icon"
        :status="agent.status"
        :logs="agent.logs"
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
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import AgentCard from '../components/AgentCard.vue'
import JudgeCard from '../components/JudgeCard.vue'
import FlowConnector from '../components/FlowConnector.vue'
import { useDetectionDemo } from '../composables/useDetectionDemo'

const title = ref('')
const imageFile = ref(null)
const imagePreview = ref('')

const { running, evidenceAgents, judge, verdict, startDemo, resetDemo } = useDetectionDemo()

const canStart = computed(() => {
  return title.value.trim().length > 0 && !!imageFile.value
})

function handleFileChange(event) {
  const file = event.target.files?.[0]
  if (!file) return

  imageFile.value = file
  imagePreview.value = URL.createObjectURL(file)
}

function resetAll() {
  title.value = ''
  imageFile.value = null
  imagePreview.value = ''
  resetDemo()
}
</script>