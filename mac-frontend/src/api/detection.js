import request from './request'

export function analyzeDetection(data) {
  const formData = new FormData()
  formData.append('title', data?.title || '')

  if (data?.imageFile) {
    formData.append('image', data.imageFile)
  }

  return request.post('/detection/analyze', formData)
}
