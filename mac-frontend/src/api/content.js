import request from './request'

export function getKnowledgeArticles(params) {
  return request.get('/knowledge/articles', { params })
}

export function getKnowledgeStats(params) {
  return request.get('/knowledge/stats', { params })
}

export function getHistoryRecords(params) {
  return request.get('/history', { params })
}

export function getHistorySummary() {
  return request.get('/history/summary')
}

export function getHistoryDetail(id) {
  return request.get(`/history/${id}`)
}

export function updateHistoryReview(id, payload) {
  return request.patch(`/history/${id}/review`, payload)
}

export function deleteHistoryRecord(id) {
  return request.delete(`/history/${id}`)
}

export function getSystemManual() {
  return request.get('/manual')
}
