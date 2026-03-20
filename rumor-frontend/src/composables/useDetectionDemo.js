import { computed, reactive, ref } from 'vue'
import { analyzeDetection } from '../api'

function isChineseResponse(meta = {}) {
  return String(meta?.response_language || '').toLowerCase().startsWith('zh')
}

function localizeVerdict(result = {}, meta = {}) {
  const next = {
    verdict: result?.verdict || '',
    category: result?.category || '',
    confidence: result?.confidence || 0,
    reasoning: result?.reasoning || ''
  }

  if (!isChineseResponse(meta)) {
    return next
  }

  const verdictMap = {
    True: '真实',
    Fake: '虚假',
    Error: '错误'
  }
  const categoryMap = {
    original: '原始新闻',
    textual_veracity_distortion: '文本事实失真',
    visual_veracity_distortion: '视觉事实失真',
    mismatch: '图文不匹配',
    api_error: '接口错误'
  }

  return {
    ...next,
    verdict: verdictMap[next.verdict] || next.verdict,
    category: categoryMap[next.category] || next.category
  }
}

function createIdleAgent(key, title, subtitle, icon) {
  return {
    key,
    title,
    subtitle,
    icon,
    status: 'idle',
    verdict: '',
    confidence: 0,
    excerpt: '',
    reportSections: []
  }
}

export function useDetectionDemo() {
  const running = ref(false)

  const evidenceAgents = reactive([
    createIdleAgent(
      'text',
      '文本真实性分析智能体',
      '抽取实体执行外部搜索，核验文本事实',
      new URL('../assets/text-agent.svg', import.meta.url).href
    ),
    createIdleAgent(
      'visual',
      '视觉真实性检测智能体',
      '分析图像语义与事实线索',
      new URL('../assets/visual-agent.svg', import.meta.url).href
    ),
    createIdleAgent(
      'consistency',
      '跨模态一致性智能体',
      '判断图文语义是否一致',
      new URL('../assets/consistency-agent.svg', import.meta.url).href
    )
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

  const meta = reactive({
    elapsed_ms: 0,
    model: '',
    filename: '',
    response_language: ''
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
      agent.verdict = ''
      agent.confidence = 0
      agent.excerpt = ''
      agent.reportSections = []
    })

    judge.status = 'idle'
    judge.logs = []
  }

  function applyAgentResult(agent, result) {
    agent.status = result?.status || 'done'
    agent.verdict = result?.verdict || ''
    agent.confidence = result?.confidence || 0
    agent.excerpt = result?.excerpt || result?.summary || ''
    agent.reportSections = [...(result?.report_sections || [])]
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

    evidenceAgents.forEach((agent, index) => {
      const base = createIdleAgent(agent.key, agent.title, agent.subtitle, agent.icon)
      Object.assign(evidenceAgents[index], base)
    })

    judge.status = 'idle'
    judge.logs = []
    verdict.verdict = ''
    verdict.category = ''
    verdict.confidence = 0
    verdict.reasoning = ''
    meta.elapsed_ms = 0
    meta.model = ''
    meta.filename = ''
    meta.response_language = ''
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

      Object.assign(verdict, localizeVerdict(result?.verdict, result?.meta))
      Object.assign(meta, result?.meta || {})
    } catch (error) {
      const detail = error?.response?.data?.detail || '任务执行失败，请检查后端服务或接口配置。'
      console.error('Failed to fetch detection result:', detail, error)
      evidenceAgents.forEach((agent) => {
        agent.status = 'idle'
        agent.verdict = ''
        agent.confidence = 0
        agent.excerpt = detail
        agent.reportSections = []
      })
      judge.status = 'idle'
      judge.logs = [detail]
      verdict.verdict = '错误'
      verdict.category = '接口错误'
      verdict.confidence = 0
      verdict.reasoning = detail
      meta.elapsed_ms = 0
      meta.model = ''
      meta.filename = ''
      meta.response_language = ''
    } finally {
      running.value = false
    }
  }

  return {
    running,
    evidenceAgents,
    judge,
    verdict,
    meta,
    startDemo,
    resetDemo
  }
}
