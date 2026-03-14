import { computed, reactive, ref } from 'vue'
import { analyzeDetection } from '../api'

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

  function formatDuration(durationMs = 0) {
    if (!durationMs) return '0 ms'
    if (durationMs < 1000) return `${durationMs} ms`
    return `${(durationMs / 1000).toFixed(2)} s`
  }

  function applyRunningState() {
    evidenceAgents.forEach((agent) => {
      agent.status = 'collecting'
      agent.logs = ['后端并行任务已启动，等待返回真实分析结果...']
    })

    judge.status = 'idle'
    judge.logs = []
  }

  function applyAgentResult(agent, result) {
    agent.status = result?.status || 'done'
    agent.logs = [...(result?.logs || [])]

    if (result?.duration_ms) {
      agent.logs.push(`阶段耗时：${formatDuration(result.duration_ms)}`)
    }
  }

  function applyJudgeResult(result, meta) {
    judge.status = result?.status || 'done'
    judge.logs = [...(result?.logs || [])]

    if (result?.duration_ms) {
      judge.logs.push(`裁决耗时：${formatDuration(result.duration_ms)}`)
    }

    if (meta?.elapsed_ms) {
      judge.logs.push(`端到端总耗时：${formatDuration(meta.elapsed_ms)}`)
    }
  }

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
    if (running.value) return
    resetDemo()
    running.value = true
    applyRunningState()

    try {
      const result = await analyzeDetection(payload)
      const agentResults = result?.agents || {}

      applyAgentResult(evidenceAgents[0], agentResults.text_analysis)
      applyAgentResult(evidenceAgents[1], agentResults.visual_investigate)
      applyAgentResult(evidenceAgents[2], agentResults.consistency_check)

      if (allEvidenceDone.value) {
        applyJudgeResult(result?.judge, result?.meta)
      }

      Object.assign(verdict, result?.verdict || {})
    } catch (error) {
      const detail = error?.response?.data?.detail || '任务执行失败，请检查后端服务或接口配置。'
      console.error('Failed to fetch detection result:', detail, error)
      evidenceAgents.forEach((agent) => {
        agent.status = 'idle'
        agent.logs = [detail]
      })
      judge.status = 'idle'
      judge.logs = [detail]
      verdict.verdict = 'Error'
      verdict.category = 'api_error'
      verdict.confidence = 0
      verdict.reasoning = detail
    } finally {
      running.value = false
    }
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
