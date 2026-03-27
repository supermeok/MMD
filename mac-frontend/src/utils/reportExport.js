const REPORT_STORAGE_KEY = 'rumor_detection_latest_report'

export function sanitizeFilename(value = '') {
  return value.replace(/[\\/:*?"<>|]/g, '').replace(/\s+/g, '_').slice(0, 36) || 'detection_report'
}

export function splitLongParagraph(paragraph = '', maxLength = 220) {
  const normalized = String(paragraph || '').trim()
  if (!normalized) return []
  if (normalized.length <= maxLength) return [normalized]

  const chunks = []
  let remaining = normalized

  while (remaining.length > maxLength) {
    let splitIndex = Math.max(
      remaining.lastIndexOf('。', maxLength),
      remaining.lastIndexOf('；', maxLength),
      remaining.lastIndexOf('，', maxLength),
      remaining.lastIndexOf('. ', maxLength),
      remaining.lastIndexOf('; ', maxLength),
      remaining.lastIndexOf(', ', maxLength),
      remaining.lastIndexOf(' ', maxLength)
    )

    if (splitIndex < Math.floor(maxLength * 0.5)) {
      splitIndex = maxLength
    } else if (remaining[splitIndex] !== ' ') {
      splitIndex += 1
    }

    chunks.push(remaining.slice(0, splitIndex).trim())
    remaining = remaining.slice(splitIndex).trim()
  }

  if (remaining) {
    chunks.push(remaining)
  }

  return chunks
}

export function formatPdfParagraphs(content = '') {
  const source = String(content || '').replace(/\r\n/g, '\n').trim()
  if (!source) return ['--']

  return source
    .split(/\n{2,}/)
    .flatMap((paragraph) => splitLongParagraph(paragraph))
    .filter(Boolean)
}

export function createReportSnapshot({ title = '', meta = {}, judge = {}, verdict = {}, evidenceAgents = [] } = {}) {
  return {
    generatedAt: new Date().toLocaleString('zh-CN', { hour12: false }),
    title,
    meta: {
      elapsed_ms: meta?.elapsed_ms || 0,
      model: meta?.model || '',
      filename: meta?.filename || '',
      response_language: meta?.response_language || ''
    },
    judge: {
      title: judge?.title || '综合裁决智能体',
      subtitle: judge?.subtitle || '',
      status: judge?.status || 'done',
      logs: [...(judge?.logs || [])]
    },
    verdict: {
      verdict: verdict?.verdict || '',
      category: verdict?.category || '',
      confidence: verdict?.confidence || 0,
      reasoning: verdict?.reasoning || ''
    },
    evidenceAgents: (evidenceAgents || []).map((agent) => ({
      key: agent?.key || '',
      title: agent?.title || '',
      subtitle: agent?.subtitle || '',
      status: agent?.status || 'done',
      verdict: agent?.verdict || '',
      confidence: agent?.confidence || 0,
      excerpt: agent?.excerpt || '',
      reportSections: [...(agent?.reportSections || [])]
    }))
  }
}

export function saveReportSnapshot(snapshot) {
  sessionStorage.setItem(REPORT_STORAGE_KEY, JSON.stringify(snapshot))
}

export function loadReportSnapshot() {
  const raw = sessionStorage.getItem(REPORT_STORAGE_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export async function exportReportPdf(element, filenameBase = 'detection_report') {
  const { default: html2pdf } = await import('html2pdf.js')
  const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')
  const filename = `${sanitizeFilename(filenameBase)}_${stamp}.pdf`

  await html2pdf()
    .set({
      margin: [10, 10, 12, 10],
      filename,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff'
      },
      jsPDF: {
        unit: 'mm',
        format: 'a4',
        orientation: 'portrait'
      },
      pagebreak: {
        mode: ['css', 'legacy', 'avoid-all'],
        before: '.pdf-page-break-before',
        avoid: ['.pdf-report__summary-card', '.pdf-report__detail', '.pdf-report__block']
      }
    })
    .from(element)
    .save()
}
