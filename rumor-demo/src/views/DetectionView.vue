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

        <el-form label-position="top">
          <el-form-item label="新闻标题">
            <el-input
              v-model="title"
              type="textarea"
              :rows="4"
              resize="none"
              placeholder="请输入新闻标题，例如：某地突发重大事件，现场图片曝光..."
            />
          </el-form-item>

          <el-form-item label="新闻图片">
            <div class="upload-row">
              <el-upload
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

              <div v-if="imagePreview" class="image-preview-wrap">
                <img :src="imagePreview" alt="preview" class="image-preview" />
              </div>
            </div>
          </el-form-item>

          <el-space wrap>
            <el-button
              type="primary"
              size="large"
              :disabled="!canStart || running"
              @click="startDetection"
            >
              {{ running ? '分析进行中...' : '开始分析检测' }}
            </el-button>
            <el-button size="large" :disabled="running" @click="resetAll">
              取消上传
            </el-button>
          </el-space>
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
  </div>
</template>

<script setup>
import { computed, ref, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import AgentCard from '../components/AgentCard.vue'
import JudgeCard from '../components/JudgeCard.vue'
import FlowConnector from '../components/FlowConnector.vue'
import { useDetectionDemo } from '../composables/useDetectionDemo'

const router = useRouter()

const title = ref('')
const imageFile = ref(null)
const imagePreview = ref('')

const { running, evidenceAgents, judge, verdict, startDemo, resetDemo } = useDetectionDemo()

const canStart = computed(() => {
  return title.value.trim().length > 0 && !!imageFile.value
})

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

function handleUploadChange(uploadFile) {
  const raw = uploadFile.raw
  if (!raw) return

  revokePreview()
  imageFile.value = raw
  imagePreview.value = URL.createObjectURL(raw)
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

function resetAll() {
  title.value = ''
  imageFile.value = null
  revokePreview()
  imagePreview.value = ''
  resetDemo()
}

onBeforeUnmount(() => {
  revokePreview()
})
</script>