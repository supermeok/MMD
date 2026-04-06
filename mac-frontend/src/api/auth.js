import request from './request'

export function login(data) {
  return request.post('/auth/login', data)
}

export function register(data) {
  return request.post('/auth/register', data)
}

export function getCurrentUser() {
  return request.get('/auth/me')
}

export function logout() {
  return request.post('/auth/logout')
}

export function getUserProfile() {
  return request.get('/auth/profile')
}

export function updateProfile(data) {
  return request.patch('/auth/profile', data)
}

export function uploadAvatar(formData) {
  return request.post('/auth/avatar', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
