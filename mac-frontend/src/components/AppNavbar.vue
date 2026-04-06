<template>
  <header class="app-navbar">
    <button type="button" class="app-navbar__brand" @click="goTo('/')">
      <span class="app-navbar__brand-dot"></span>
      <span class="app-navbar__brand-text">
        <strong>多智裁决</strong>
        <small>基于多智能体裁决的谣言检测系统</small>
      </span>
    </button>

    <nav class="app-navbar__links">
      <button
        v-for="item in navItems"
        :key="item.path"
        type="button"
        class="app-navbar__link"
        :class="{ 'is-active': isActive(item.path) }"
        @click="goTo(item.path)"
      >
        {{ item.label }}
      </button>

      <div v-if="isLoggedIn" class="app-navbar__user">
        <el-popover
          placement="bottom-end"
          :width="320"
          trigger="click"
          v-model:visible="showProfileCard"
        >
          <template #reference>
            <div class="app-navbar__avatar">
              <img :src="userAvatar" alt="用户头像" />
            </div>
          </template>
          
          <div class="user-profile-card">
            <div class="user-profile-card__header">
              <div class="user-profile-card__avatar-wrapper">
                <img :src="userAvatar" alt="头像" class="user-profile-card__avatar" />
                <label class="user-profile-card__avatar-upload">
                  <input type="file" accept="image/*" hidden @change="handleAvatarChange" />
                  <span class="upload-icon">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                      <path d="M12 16l-6-6h4V4h4v6h4l-6 6zm-6 2v2h12v-2H6z"/>
                    </svg>
                  </span>
                </label>
              </div>
              <div class="user-profile-card__info">
                <h3 class="user-profile-card__name">{{ userProfile.username }}</h3>
                <p class="user-profile-card__email">{{ userProfile.email || '未设置邮箱' }}</p>
              </div>
            </div>
            
            <el-form 
              v-if="isEditing" 
              :model="editForm" 
              label-position="top" 
              class="user-profile-card__form"
            >
              <el-form-item label="用户名">
                <el-input v-model="editForm.username" size="small" />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="editForm.email" size="small" />
              </el-form-item>
              <el-form-item label="新密码">
                <el-input v-model="editForm.newPassword" type="password" size="small" placeholder="留空则不修改" />
              </el-form-item>
              <el-form-item label="确认密码">
                <el-input v-model="editForm.confirmPassword" type="password" size="small" />
              </el-form-item>
              <div class="user-profile-card__actions">
                <el-button size="small" @click="cancelEdit">取消</el-button>
                <el-button type="primary" size="small" :loading="saving" @click="saveProfile">保存</el-button>
              </div>
            </el-form>
            
            <div v-else class="user-profile-card__body">
              <div class="user-profile-card__item">
                <span class="item-label">用户名</span>
                <span class="item-value">{{ userProfile.username }}</span>
              </div>
              <div class="user-profile-card__item">
                <span class="item-label">邮箱</span>
                <span class="item-value">{{ userProfile.email || '未设置' }}</span>
              </div>
              <div class="user-profile-card__item">
                <span class="item-label">密码</span>
                <span class="item-value">••••••••</span>
              </div>
              <div class="user-profile-card__item">
                <span class="item-label">注册时间</span>
                <span class="item-value">{{ userProfile.createdAt || '未知' }}</span>
              </div>
            </div>
            
            <div v-if="!isEditing" class="user-profile-card__footer">
              <el-button size="small" class="edit-btn" @click="startEdit">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" style="margin-right: 4px;">
                  <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                </svg>
                编辑资料
              </el-button>
              <el-button size="small" type="danger" plain @click="handleLogout">
                退出登录
              </el-button>
            </div>
          </div>
        </el-popover>
      </div>
      <el-button v-else type="primary" size="small" class="app-navbar__login" @click="goTo('/login')">
        登录
      </el-button>
    </nav>
  </header>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getUserProfile, updateProfile, uploadAvatar } from '../api/auth'

const route = useRoute()
const router = useRouter()

const defaultAvatar = new URL('../assets/judge-agent.svg', import.meta.url).href

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'
const mediaBaseUrl = apiBaseUrl.replace('/api', '')

function getFullAvatarUrl(avatarPath) {
  if (!avatarPath) return defaultAvatar
  if (avatarPath.startsWith('http://') || avatarPath.startsWith('https://')) {
    return avatarPath
  }
  return mediaBaseUrl + avatarPath
}

const isLoggedIn = ref(false)
const showProfileCard = ref(false)
const isEditing = ref(false)
const saving = ref(false)

const userProfile = reactive({
  username: '',
  email: '',
  avatar: '',
  createdAt: ''
})

const editForm = reactive({
  username: '',
  email: '',
  newPassword: '',
  confirmPassword: ''
})

const userAvatar = computed(() => {
  return getFullAvatarUrl(userProfile.avatar)
})

const navItems = [
  { label: '首页', path: '/' },
  { label: '开始检测', path: '/detect' },
  { label: '知识库', path: '/knowledge' },
  { label: '历史记录', path: '/history' },
  { label: '系统手册', path: '/manual' }
]

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

function goTo(path) {
  if (route.path === path) return
  router.push(path)
}

function startEdit() {
  editForm.username = userProfile.username
  editForm.email = userProfile.email || ''
  editForm.newPassword = ''
  editForm.confirmPassword = ''
  isEditing.value = true
}

function cancelEdit() {
  isEditing.value = false
}

async function saveProfile() {
  if (editForm.newPassword && editForm.newPassword !== editForm.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  
  saving.value = true
  try {
    await updateProfile({
      username: editForm.username,
      email: editForm.email,
      password: editForm.newPassword || undefined
    })
    
    userProfile.username = editForm.username
    userProfile.email = editForm.email
    localStorage.setItem('username', editForm.username)
    
    ElMessage.success('资料更新成功')
    isEditing.value = false
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  } finally {
    saving.value = false
  }
}

async function handleAvatarChange(event) {
  const file = event.target.files?.[0]
  if (!file) return
  
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 2MB')
    return
  }
  
  try {
    const formData = new FormData()
    formData.append('avatar', file)
    const res = await uploadAvatar(formData)
    userProfile.avatar = res.avatar_url
    ElMessage.success('头像更新成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '头像上传失败')
  }
}

async function loadUserProfile() {
  try {
    const res = await getUserProfile()
    userProfile.username = res.username || ''
    userProfile.email = res.email || ''
    userProfile.avatar = res.avatar || ''
    userProfile.createdAt = res.created_at || ''
  } catch (error) {
    console.error('Failed to load user profile:', error)
  }
}

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  isLoggedIn.value = false
  showProfileCard.value = false
  ElMessage.success('已退出登录')
  router.push('/login')
}

onMounted(() => {
  const token = localStorage.getItem('token')
  isLoggedIn.value = !!token
  
  if (isLoggedIn.value) {
    userProfile.username = localStorage.getItem('username') || ''
    loadUserProfile()
  }
})
</script>
