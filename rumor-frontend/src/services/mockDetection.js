function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

const evidenceStepMap = {
  text: ['提取标题关键实体', '检索外部事实知识', '完成文本真实性判断'],
  visual: ['识别图像主体信息', '分析视觉语义线索', '完成视觉真实性判断'],
  consistency: ['对齐图文语义表示', '比较标题与图像内容', '完成一致性检测']
}

const evidenceDelayMap = {
  text: 650,
  visual: 820,
  consistency: 720
}

export async function runMockEvidenceAgent(agent) {
  agent.status = 'collecting'
  agent.logs = []

  const steps = evidenceStepMap[agent.key] || ['处理中...']
  const baseDelay = evidenceDelayMap[agent.key] || 700

  for (const step of steps) {
    agent.logs.push(step)
    await sleep(baseDelay + Math.random() * 450)
  }

  agent.status = 'done'
}

export async function runMockJudge(judge) {
  judge.status = 'collecting'
  judge.logs = []

  const steps = [
    '接收文本、视觉、一致性三路证据',
    '执行冲突对齐与可信度融合',
    '生成最终裁决与可解释结论'
  ]

  for (const step of steps) {
    judge.logs.push(step)
    await sleep(900)
  }

  judge.status = 'done'
}