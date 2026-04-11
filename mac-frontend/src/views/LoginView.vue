<template>
  <div class="login-page">
    <div class="bg-grid"></div>
    <div class="cyber-grid"></div>
    
    <div class="particle-container">
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
      <div class="particle"></div>
    </div>
    
    <div class="login-container">
      <div class="login-left">
        <div class="login-brand animate-slide-up">
          <div class="login-brand__dot"></div>
          <h1 class="login-brand__title tech-gradient-text">多智裁决</h1>
          <p class="login-brand__subtitle">基于多智能体裁决的多模态谣言检测系统</p>
        </div>
        
        <div class="login-agents">
          <div class="login-agents__top">
            <div class="login-agent hover-lift stagger-1">
              <div class="login-agent__icon">
                <img :src="textIcon" alt="文本智能体" />
              </div>
              <span class="login-agent__name">文本分析</span>
            </div>
            <div class="login-agent hover-lift stagger-2">
              <div class="login-agent__icon">
                <img :src="visualIcon" alt="视觉智能体" />
              </div>
              <span class="login-agent__name">视觉检测</span>
            </div>
            <div class="login-agent hover-lift stagger-3">
              <div class="login-agent__icon">
                <img :src="consistencyIcon" alt="一致性智能体" />
              </div>
              <span class="login-agent__name">一致性判断</span>
            </div>
          </div>
          
          <div class="login-agents__flow">
            <div class="flow-line"></div>
            <div class="flow-arrow"></div>
          </div>
          
          <div class="login-agents__bottom">
            <div class="login-agent login-agent--judge animate-float">
              <div class="login-agent__icon login-agent__icon--judge">
                <img :src="judgeIcon" alt="裁决智能体" />
              </div>
              <span class="login-agent__name">综合裁决</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="login-right">
        <div class="login-form-wrapper animate-slide-right">
          <div class="login-form-header">
            <h2>{{ isLogin ? '欢迎回来' : '创建账户' }}</h2>
            <p>{{ isLogin ? '登录您的账户以继续使用系统' : '注册新账户开始使用系统' }}</p>
          </div>
          
          <el-form
            ref="formRef"
            :model="formData"
            :rules="formRules"
            class="login-form"
            @submit.prevent="handleSubmit"
          >
            <el-form-item prop="username">
              <el-input
                v-model="formData.username"
                placeholder="请输入用户名"
                size="large"
                prefix-icon="User"
              />
            </el-form-item>
            
            <el-form-item prop="password">
              <el-input
                v-model="formData.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            
            <el-form-item v-if="!isLogin" prop="confirmPassword">
              <el-input
                v-model="formData.confirmPassword"
                type="password"
                placeholder="请确认密码"
                size="large"
                prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="login-submit-btn neon-button"
                :loading="loading"
                @click="handleSubmit"
              >
                {{ isLogin ? '登录' : '注册' }}
              </el-button>
            </el-form-item>
          </el-form>
          
          <div class="login-switch">
            <span>{{ isLogin ? '还没有账户？' : '已有账户？' }}</span>
            <el-button type="text" class="glitch" @click="toggleMode">
              {{ isLogin ? '立即注册' : '立即登录' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login, register } from '../api/auth'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const isLogin = ref(true)

const formData = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (!isLogin.value) {
    if (!value) {
      callback(new Error('请确认密码'))
    } else if (value !== formData.password) {
      callback(new Error('两次输入的密码不一致'))
    } else {
      callback()
    }
  } else {
    callback()
  }
}

const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 30, message: '密码长度在 6 到 30 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const textIcon = new URL('../assets/text-agent.svg', import.meta.url).href
const visualIcon = new URL('../assets/visual-agent.svg', import.meta.url).href
const consistencyIcon = new URL('../assets/consistency-agent.svg', import.meta.url).href
const judgeIcon = new URL('../assets/judge-agent.svg', import.meta.url).href

function toggleMode() {
  isLogin.value = !isLogin.value
  formRef.value?.resetFields()
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  
  try {
    if (isLogin.value) {
      const res = await login({
        username: formData.username,
        password: formData.password
      })
      localStorage.setItem('token', res.token)
      localStorage.setItem('username', res.username || formData.username)
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      await register({
        username: formData.username,
        password: formData.password
      })
      ElMessage.success('注册成功，请登录')
      isLogin.value = true
      formRef.value?.resetFields()
    }
  } catch (error) {
    const message = error.response?.data?.detail || (isLogin.value ? '登录失败' : '注册失败')
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}
</script>
