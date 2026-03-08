<template>
  <div class="home-page">
    <div class="home-bg"></div>

    <header class="home-header">
      <div class="brand">Rumor Detection Demo</div>
      <router-link to="/detect" class="header-link">进入检测页</router-link>
    </header>

    <main class="home-main">
      <section class="hero-section">
        <div class="hero-left">
          <div class="home-tag">多智能体裁决 · 多模态谣言检测</div>
          <h1>基于多智能体裁决的多模态谣言检测演示平台</h1>
          <p class="hero-desc">
            系统通过文本真实性核验、视觉真实性核验、跨模态一致性检测三个证据收集智能体并行工作，
            再由综合裁决智能体融合三路证据，输出真假判断、类别、置信度与解释结果。
          </p>

          <div class="hero-actions">
            <button class="home-primary-btn" @click="goDetect">开始检测分析</button>
            <router-link to="/detect" class="home-ghost-btn">直接进入演示</router-link>
          </div>
        </div>

        <div class="hero-right">
          <div class="hero-card">
            <div class="hero-card-title">系统核心流程</div>
            <div class="agent-grid-preview">
              <div class="mini-agent-card">
                <img :src="textIcon" alt="文本智能体" />
                <span>文本真实性</span>
              </div>
              <div class="mini-agent-card">
                <img :src="visualIcon" alt="视觉智能体" />
                <span>视觉真实性</span>
              </div>
              <div class="mini-agent-card">
                <img :src="consistencyIcon" alt="一致性智能体" />
                <span>跨模态一致性</span>
              </div>
            </div>

            <div class="mini-flow-line"></div>

            <div class="judge-preview">
              <img :src="judgeIcon" alt="裁决智能体" />
              <span>综合裁决智能体</span>
            </div>
          </div>
        </div>
      </section>

      <section class="feature-section">
        <div class="feature-card">
          <h3>并行证据收集</h3>
          <p>三个证据智能体同时工作，突出多智能体协同特征与过程可视化效果。</p>
        </div>

        <div class="feature-card">
          <h3>可解释裁决</h3>
          <p>不仅输出真假结论，还展示类别、置信度以及裁决原因。</p>
        </div>

        <div class="feature-card">
          <h3>竞赛演示友好</h3>
          <p>结构清晰、动画明显、流程完整，适合答辩展示和项目讲解。</p>
        </div>
      </section>
    </main>
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