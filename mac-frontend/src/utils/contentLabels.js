export function getBinaryLabel(type = '') {
  const normalized = String(type)
  if (normalized === 'True' || normalized === '真实') return '真实'
  if (normalized === 'Fake' || normalized === '虚假') return '虚假'
  if (normalized === 'Uncertain' || normalized === '待定') return '待定'
  return normalized || '未知'
}

export function getBinaryTagType(type = '') {
  const normalized = String(type)
  if (normalized === 'True' || normalized === '真实') return 'success'
  if (normalized === 'Fake' || normalized === '虚假') return 'danger'
  if (normalized === 'Uncertain' || normalized === '待定') return 'warning'
  return 'info'
}

export function getFakeTypeLabel(type = '') {
  const labels = {
    original: '真实新闻',
    textual_veracity_distortion: '文本虚假',
    visual_veracity_distortion: '视觉虚假',
    mismatch: '图文不一致',
    '原始新闻': '真实新闻',
    '文本事实失真': '文本虚假',
    '视觉事实失真': '视觉虚假',
    '图文不匹配': '图文不一致',
    真实: '真实新闻',
    文本虚假: '文本虚假',
    视觉虚假: '视觉虚假',
    图文不一致: '图文不一致'
  }
  return labels[type] || type || '未分类'
}

export function getFakeTypeColor(type = '') {
  const colors = {
    original: 'success',
    textual_veracity_distortion: 'warning',
    visual_veracity_distortion: 'danger',
    mismatch: 'info',
    '原始新闻': 'success',
    '文本事实失真': 'warning',
    '视觉事实失真': 'danger',
    '图文不匹配': 'info',
    真实: 'success',
    文本虚假: 'warning',
    视觉虚假: 'danger',
    图文不一致: 'info'
  }
  return colors[type] || 'info'
}

export function getKnowledgeThemeLabel(theme = '', isChinese = true) {
  const labels = {
    '政治与公共议题': {
      zh: '政治与公共议题',
      en: 'Politics & Public Affairs'
    },
    '通用视觉场景': {
      zh: '通用视觉场景',
      en: 'General Visual Scenes'
    },
    '新闻报道场景': {
      zh: '新闻报道场景',
      en: 'News Reporting Scenes'
    },
    '社交媒体内容': {
      zh: '社交媒体内容',
      en: 'Social Media Content'
    },
    '娱乐与名人': {
      zh: '娱乐与名人',
      en: 'Entertainment & Celebrity'
    },
    '文本生成改写': {
      zh: '文本生成改写',
      en: 'Text Rewrite'
    },
    '科学与科普': {
      zh: '科学与科普',
      en: 'Science & Popular Science'
    },
    '综合开放域': {
      zh: '综合开放域',
      en: 'Open Domain'
    }
  }

  const item = labels[theme]
  if (!item) return theme || (isChinese ? '未分类主题' : 'Uncategorized')
  return isChinese ? item.zh : item.en
}

export function getKnowledgeThemeType(theme = '') {
  const colors = {
    '政治与公共议题': 'danger',
    '通用视觉场景': 'warning',
    '新闻报道场景': 'primary',
    '社交媒体内容': 'info',
    '娱乐与名人': 'success',
    '文本生成改写': 'warning',
    '科学与科普': 'success',
    '综合开放域': 'info'
  }
  return colors[theme] || 'info'
}

export const knowledgeThemeOptions = [
  {
    value: '政治与公共议题',
    labelZh: '政治与公共议题',
    labelEn: 'Politics & Public Affairs'
  },
  {
    value: '通用视觉场景',
    labelZh: '通用视觉场景',
    labelEn: 'General Visual Scenes'
  },
  {
    value: '新闻报道场景',
    labelZh: '新闻报道场景',
    labelEn: 'News Reporting Scenes'
  },
  {
    value: '社交媒体内容',
    labelZh: '社交媒体内容',
    labelEn: 'Social Media Content'
  },
  {
    value: '娱乐与名人',
    labelZh: '娱乐与名人',
    labelEn: 'Entertainment & Celebrity'
  },
  {
    value: '文本生成改写',
    labelZh: '文本生成改写',
    labelEn: 'Text Rewrite'
  },
  {
    value: '科学与科普',
    labelZh: '科学与科普',
    labelEn: 'Science & Popular Science'
  }
]

export function getReviewStatusLabel(status = '') {
  const labels = {
    pending: '待复查',
    approved: '复查确认',
    corrected: '人工改判',
    flagged: '继续跟进'
  }
  return labels[status] || '待复查'
}

export function getReviewStatusType(status = '') {
  const types = {
    pending: 'warning',
    approved: 'success',
    corrected: 'danger',
    flagged: 'info'
  }
  return types[status] || 'warning'
}

export function formatDateTime(value = '') {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

export function formatConfidence(value = 0) {
  return `${Number(value || 0)}%`
}

export const AUTO_MANUAL_VERDICT = '__AUTO__'

export const reviewStatusOptions = [
  { label: '待复查', value: 'pending' },
  { label: '复查确认', value: 'approved' },
  { label: '人工改判', value: 'corrected' },
  { label: '继续跟进', value: 'flagged' }
]

export const manualVerdictOptions = [
  { label: '沿用自动结论', value: AUTO_MANUAL_VERDICT },
  { label: '人工判定为真实', value: 'True' },
  { label: '人工判定为虚假', value: 'Fake' },
  { label: '暂不下结论', value: 'Uncertain' }
]
