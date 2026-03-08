import { computed, reactive, ref } from 'vue'
import { runMockEvidenceAgent, runMockJudge } from '../services/mockDetection'

export function useDetectionDemo() {
  const running = ref(false)

  const evidenceAgents = reactive([
    {
      key: 'text',
      title: '文本真实性智能体',
      subtitle: '抽取实体并核验文本事实',
      icon: new URL('../assets/text-agent.svg', import.meta.url).href,
      status: 'idle',
      logs: []
    },
    {
      key: 'visual',
      title: '视觉真实性智能体',
      subtitle: '分析图像语义与事实线索',
      icon: new URL('../assets/visual-agent.svg', import.meta.url).href,
      status: 'idle',
      logs: []
    },
    {
      key: 'consistency',
      title: '跨模态一致性智能体',
      subtitle: '判断图文语义是否一致',
      icon: new URL('../assets/consistency-agent.svg', import.meta.url).href,
      status: 'idle',
      logs: []
    }
  ])

  const judge = reactive({
    title: '综合裁决智能体',
    subtitle: '融合三份证据并输出最终结论',
    icon: new URL('../assets/judge-agent.svg', import.meta.url).href,
    status: 'idle',
    logs: []
  })

  const verdict = reactive({
    verdict: 'Fake',
    category: 'mismatch',
    confidence: 93,
    reasoning: '三路证据显示标题与图片存在明显不一致，综合裁决为疑似谣言。'
  })

  const allEvidenceDone = computed(() => evidenceAgents.every((item) => item.status === 'done'))

  function resetDemo() {
    running.value = false

    evidenceAgents.forEach((agent) => {
      agent.status = 'idle'
      agent.logs = []
    })

    judge.status = 'idle'
    judge.logs = []
  }

  async function startDemo(payload = {}) {
    if (running.value) return
    resetDemo()
    running.value = true

    const tasks = evidenceAgents.map((agent) => runMockEvidenceAgent(agent, payload))
    await Promise.all(tasks)

    if (allEvidenceDone.value) {
      await runMockJudge(judge, payload)
    }

    running.value = false
  }

  return {
    running,
    evidenceAgents,
    judge,
    verdict,
    startDemo,
    resetDemo
  }
}