<template>
  <div class="home-page">
    <div class="bg-grid"></div>
    <div class="bg-glow bg-glow-left"></div>
    <div class="bg-glow bg-glow-right"></div>

    <div class="home-container">
      <section class="hero-layout">
        <div class="hero-left">
          <h1>基于多智能体裁决的谣言检测系统</h1>

          <el-button
            type="primary"
            size="large"
            class="start-btn"
            @click="goDetect"
          >
            开始检测
          </el-button>
        </div>

        <div class="hero-right">
          <el-card shadow="never" class="flow-card">
            <template #header>
              <div class="flow-card-header">
                <span>系统核心流程</span>
              </div>
            </template>

            <div class="flow-top">
              <div class="flow-agent">
                <div class="flow-agent-icon">
                  <img :src="textIcon" alt="文本真实性" />
                </div>
                <div class="flow-agent-title">文本真实性分析</div>
              </div>

              <div class="flow-agent">
                <div class="flow-agent-icon">
                  <img :src="visualIcon" alt="视觉真实性" />
                </div>
                <div class="flow-agent-title">视觉真实性检测</div>
              </div>

              <div class="flow-agent">
                <div class="flow-agent-icon">
                  <img :src="consistencyIcon" alt="跨模态一致性" />
                </div>
                <div class="flow-agent-title">跨模态一致性判断</div>
              </div>
            </div>

            <div class="flow-merge">
              <span></span>
            </div>

            <div class="flow-judge">
              <div class="judge-robot">
                <img :src="judgeIcon" alt="综合裁决智能体" />
              </div>
              <div class="judge-title">综合裁决智能体</div>
            </div>
          </el-card>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const textIcon = new URL('../assets/text-agent.svg', import.meta.url).href
const visualIcon = new URL('../assets/visual-agent.svg', import.meta.url).href
const consistencyIcon = new URL('../assets/consistency-agent.svg', import.meta.url).href
const judgeIcon = new URL('../assets/judge-agent.svg', import.meta.url).href

function goDetect() {
  router.push('/detect')
}
</script>

