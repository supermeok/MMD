import { computed, reactive, ref } from 'vue'
import { runMockEvidenceAgent, runMockJudge } from '../services/mockDetection'
import { getVerdict } from '../api'

export function useDetectionDemo() {
  const running = ref(false)

  const evidenceAgents = reactive([
    {
      key: 'text',
      title: '文本真实性分析智能体',
      subtitle: '抽取实体执行外部搜索，核验文本事实',
      icon: new URL('../assets/text-agent.svg', import.meta.url).href,
      status: 'idle',
      logs: []
    },
    {
      key: 'visual',
      title: '视觉真实性检测智能体',
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
    verdict: '',
    category: '',
    confidence: 0,
    reasoning: ''
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
    verdict.verdict = ''
    verdict.category = ''
    verdict.confidence = 0
    verdict.reasoning = ''
  }

  async function startDemo(payload = {}) {
    // console.log('startDemo payload:', payload)
    if (running.value) return
    resetDemo()
    running.value = true

    const tasks = evidenceAgents.map((agent) => runMockEvidenceAgent(agent, payload))
    await Promise.all(tasks)

    if (allEvidenceDone.value) {
      await runMockJudge(judge, payload)
      try {
        const result = await getVerdict(payload)
        Object.assign(verdict, result)
      } catch (error) {
        console.error('Failed to fetch verdict:', error)
        verdict.verdict = 'Error'
        verdict.category = 'api_error'
        verdict.confidence = 0
        verdict.reasoning = '后端请求失败，请检查服务是否启动或跨域配置。'
      }
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
