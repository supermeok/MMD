import { computed, reactive, ref } from 'vue'
import { analyzeDetection, getHistoryDetail } from '../api'

const LATEST_HISTORY_STORAGE_KEY = 'mac_judge_latest_history_id'

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

function createHistoryVerdict(detail = {}) {
  return {
    verdict: detail?.item?.auto_verdict || detail?.judge?.verdict?.verdict || '',
    category: detail?.item?.auto_category || detail?.judge?.verdict?.category || '',
    confidence: detail?.item?.auto_confidence || detail?.judge?.verdict?.confidence || 0,
    reasoning: detail?.item?.auto_reasoning || detail?.judge?.verdict?.reasoning || ''
  }
}

export function useDetectionDemo() {
  const running = ref(false)
  const historyId = ref('')

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

  function sanitizeJudgeLogs(logs = []) {
    return [...(logs || [])].filter((log) => {
      const normalized = String(log || '').trim()
      return !normalized.startsWith('裁决耗时：') && !normalized.startsWith('端到端总耗时：')
    })
  }

  function setStoredHistoryId(value = '') {
    historyId.value = value || ''

    if (historyId.value) {
      sessionStorage.setItem(LATEST_HISTORY_STORAGE_KEY, historyId.value)
      return
    }

    sessionStorage.removeItem(LATEST_HISTORY_STORAGE_KEY)
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
    agent.reportSections = [...(result?.report_sections || result?.reportSections || [])]
  }

  function applyJudgeResult(result) {
    const nextLogs = sanitizeJudgeLogs(result?.logs || [])

    judge.status = result?.status || 'done'

    judge.logs = nextLogs
  }

  function assignMeta(source = {}) {
    meta.elapsed_ms = source?.elapsed_ms || 0
    meta.model = source?.model || ''
    meta.filename = source?.filename || ''
    meta.response_language = source?.response_language || ''
  }

  function resetDemo(options = {}) {
    const clearPersisted = options.clearPersisted !== false
    running.value = false

    if (clearPersisted) {
      setStoredHistoryId('')
    } else {
      historyId.value = ''
    }

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
    assignMeta()
  }

  function getDemoSnapshot() {
    return {
      historyId: historyId.value,
      evidenceAgents: evidenceAgents.map((agent) => ({
        key: agent.key,
        title: agent.title,
        subtitle: agent.subtitle,
        icon: agent.icon,
        status: agent.status,
        verdict: agent.verdict,
        confidence: agent.confidence,
        excerpt: agent.excerpt,
        reportSections: [...agent.reportSections]
      })),
      judge: {
        title: judge.title,
        subtitle: judge.subtitle,
        icon: judge.icon,
        status: judge.status,
        logs: [...judge.logs]
      },
      verdict: {
        verdict: verdict.verdict,
        category: verdict.category,
        confidence: verdict.confidence,
        reasoning: verdict.reasoning
      },
      meta: {
        elapsed_ms: meta.elapsed_ms,
        model: meta.model,
        filename: meta.filename,
        response_language: meta.response_language
      }
    }
  }

  function restoreFromSnapshot(snapshot = {}) {
    if (!snapshot) return false

    setStoredHistoryId(snapshot.historyId || '')

    evidenceAgents.forEach((agent, index) => {
      const source = snapshot?.evidenceAgents?.[index] || {}
      Object.assign(agent, {
        ...agent,
        status: source.status || 'idle',
        verdict: source.verdict || '',
        confidence: source.confidence || 0,
        excerpt: source.excerpt || '',
        reportSections: [...(source.reportSections || [])]
      })
    })

    judge.status = snapshot?.judge?.status || 'idle'
    judge.logs = sanitizeJudgeLogs(snapshot?.judge?.logs || [])
    verdict.verdict = snapshot?.verdict?.verdict || ''
    verdict.category = snapshot?.verdict?.category || ''
    verdict.confidence = snapshot?.verdict?.confidence || 0
    verdict.reasoning = snapshot?.verdict?.reasoning || ''
    assignMeta(snapshot?.meta || {})
    running.value = false
    return Boolean(historyId.value || verdict.verdict)
  }

  function hydrateFromHistoryDetail(detail = {}) {
    const agentResults = detail?.agents || {}

    applyAgentResult(evidenceAgents[0], agentResults.text_analysis)
    applyAgentResult(evidenceAgents[1], agentResults.visual_investigate)
    applyAgentResult(evidenceAgents[2], agentResults.consistency_check)
    applyJudgeResult(detail?.judge)
    Object.assign(verdict, localizeVerdict(createHistoryVerdict(detail), detail?.meta))
    assignMeta(detail?.meta || {})
    setStoredHistoryId(detail?.item?.id || '')
    running.value = false
  }

  async function restoreLatestResult() {
    const latestHistoryId = historyId.value || sessionStorage.getItem(LATEST_HISTORY_STORAGE_KEY) || ''
    if (!latestHistoryId) {
      return null
    }

    try {
      const detail = await getHistoryDetail(latestHistoryId)
      hydrateFromHistoryDetail(detail)
      return detail
    } catch (error) {
      console.error('Failed to restore latest detection result:', error)
      resetDemo()
      return null
    }
  }

  async function startDemo(payload = {}) {
    if (running.value) return null
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
        applyJudgeResult(result?.judge)
      }

      Object.assign(verdict, localizeVerdict(result?.verdict, result?.meta))
      assignMeta(result?.meta || {})
      setStoredHistoryId(result?.history_id || '')
      return result
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
      assignMeta()
      setStoredHistoryId('')
      return null
    } finally {
      running.value = false
    }
  }

  return {
    running,
    historyId,
    evidenceAgents,
    judge,
    verdict,
    meta,
    startDemo,
    resetDemo,
    getDemoSnapshot,
    restoreFromSnapshot,
    restoreLatestResult,
    hydrateFromHistoryDetail
  }
}
