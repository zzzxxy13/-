<template>
  <main class="dream-app">
    
    <!-- === 全局动态壁纸背景 === -->
    <div class="video-bg-container">
      <video autoplay loop muted playsinline class="dynamic-video">
        <source src="/dynamic-bg.mp4" type="video/mp4" />
      </video>
      <div class="video-overlay" :class="{ 'app-mode-overlay': stage === 'app' }"></div>
    </div>

    <!-- === 阶段 1: 封面页 === -->
    <section v-if="stage === 'cover'" class="cover-page fade-in">
      <div class="cover-outer-frame">
        <div class="cover-inner-frame">
          <div class="cover-image-crop"></div>
          <div class="cover-text-area">
            <h1>Dream Archive</h1>
            <h3>藏梦馆</h3>
            <p class="slogan">珍藏私人梦境碎片，<br>与同频灵魂共赴幻夜</p>
            <button class="custom-enter-btn" @click="enterApp">
              <span class="btn-text">ENTER</span>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- === 阶段 2: 核心系统 === -->
    <section v-else class="app-core fade-in">
      
      <!-- 左侧固定悬浮导航 -->
      <nav v-if="user" class="floating-nav fade-in">
        <div class="nav-header">
          <p class="nav-eyebrow">NAVIGATION</p>
        </div>
        <button :class="{ active: view === 'dreams' }" @click="view = 'dreams'">我的梦境</button>
        <button :class="{ active: view === 'community' }" @click="openCommunity">匿名社区</button>
        <!-- 核心：只有 ADMIN 角色才会显示管理后台按钮 -->
        <button v-if="user?.role === 'ADMIN'" :class="{ active: view === 'admin' }" @click="openAdmin">管理后台</button>
        <div class="nav-divider"></div>
        <button class="danger" @click="logout">退出登录</button>
      </nav>

      <!-- 居中主体内容区 -->
      <div class="main-content">
        
        <!-- 未登录：高定版登录面板 -->
        <div v-if="!user" class="glass-panel login-panel fade-in">
          <div class="panel-header">
            <!-- 标题动态切换 -->
            <p class="eyebrow">{{ isAdminMode ? 'Admin Portal' : 'Sign In' }}</p>
            <h2>{{ isAdminMode ? '藏梦馆管理中心' : '欢迎来到藏梦馆' }}</h2>
            <div class="title-line"></div>
          </div>
          <div class="form-grid">
            <div class="input-wrapper">
              <input v-model="auth.username" placeholder="请输入用户名" />
              <span class="focus-border"></span>
            </div>
            <div class="input-wrapper">
              <input v-model="auth.password" type="password" placeholder="请输入密码" />
              <span class="focus-border"></span>
            </div>
            
            <!-- 新增：高级流光管理员通道开关 -->
            <div class="admin-toggle-wrapper">
              <label class="admin-toggle">
                <input type="checkbox" v-model="isAdminMode" @change="handleAdminToggle" />
                <span class="toggle-slider"></span>
                <span class="toggle-label">启用管理员通道</span>
              </label>
            </div>

            <div class="actions" style="margin-top: 10px;">
              <button class="primary" @click="login">{{ isAdminMode ? '验证权限' : '进入梦境' }}</button>
              <button v-if="!isAdminMode" class="secondary" @click="register">注册档案</button>
            </div>
          </div>
          <p class="hint-message">{{ message }}</p>
        </div>

        <!-- 已登录：模块切换 -->
        <template v-else>
          <!-- 我的梦境 -->
          <div v-if="view === 'dreams'" class="fade-in">
            <div class="glass-panel">
              <p class="eyebrow">Record</p>
              <h2>记录新的梦</h2>
              <div class="form-grid">
                <input v-model="form.title" placeholder="梦境标题" class="system-input" />
                <textarea v-model="form.content" placeholder="写下梦里最清晰的片段" class="system-textarea"></textarea>
                <div class="row">
                  <input v-model="form.dreamDate" type="date" class="system-date" />
                  <select v-model.number="form.moodScore" class="system-select">
                    <option :value="1">1 星 强烈负面</option>
                    <option :value="2">2 星 偏负面</option>
                    <option :value="3">3 星 中性</option>
                    <option :value="4">4 星 偏正面</option>
                    <option :value="5">5 星 积极愉快</option>
                  </select>
                </div>
                <button class="primary" style="width: 100%; margin-top: 10px;" @click="saveDream">封存碎片</button>
              </div>
              <p class="hint-message">{{ message }}</p>
            </div>

            <div class="glass-panel">
              <p class="eyebrow">Archive</p>
              <h2>我的藏梦记录</h2>
              <div class="dream-list-container">
                <article v-for="dream in dreams" :key="dream.id" class="dream-item" @click="selectDream(dream)">
                  <div class="item-text">
                    <h3>{{ dream.title }}</h3>
                    <p>{{ dream.content }}</p>
                  </div>
                  <span class="tag">{{ dream.moodScore }} 星</span>
                </article>
              </div>
            </div>

            <div v-if="selected" class="glass-panel detail-panel fade-in">
              <p class="eyebrow">Analysis</p>
              <h2>{{ selected.title }}</h2>
              <p class="selected-dream-body">{{ selected.content }}</p>
              <div class="actions">
                <button class="primary" @click="analyzeDream(selected.id)">深度分析梦境</button>
                <button class="secondary" @click="shareDream(selected.id)">飘入匿名幻夜</button>
              </div>
              <section v-if="analysis" class="analysis-box">
                <strong class="keyword-highlight">命中关键词：{{ analysis.matchedKeywords || '暂无命中' }}</strong>
                <p class="analysis-text">{{ analysis.ruleBasedResult }}</p>
                <pre>{{ formatJson(analysis.aiResult) }}</pre>
              </section>
            </div>
          </div>

          <!-- 匿名社区 -->
          <div v-if="view === 'community'" class="glass-panel fade-in">
            <p class="eyebrow">Community</p>
            <h2>匿名幻夜社区</h2>
            <div class="dream-list-container">
              <article v-for="dream in communityDreams" :key="dream.id" class="dream-item">
                <div class="item-text">
                  <h3>{{ dream.anonymousName }} · {{ dream.title }}</h3>
                  <p>{{ dream.content }}</p>
                </div>
                <span class="tag">{{ dream.moodScore }} 星</span>
              </article>
            </div>
          </div>

          <!-- 后台管理 (监管功能版块) -->
          <div v-if="view === 'admin'" class="glass-panel fade-in">
            <p class="eyebrow">Admin</p>
            <h2>社区内容监管</h2>
            <div class="dream-list-container">
              <article v-for="dream in adminDreams" :key="dream.id" class="dream-item">
                <div class="item-text">
                  <h3>{{ dream.anonymousName }} · {{ dream.title }}</h3>
                  <p>{{ dream.content }}</p>
                  <small class="admin-status">当前状态：{{ dream.auditStatus }}</small>
                </div>
                <div class="actions">
                  <button class="secondary" @click="hideDream(dream.id)">下架违规内容</button>
                  <button class="danger" @click="deleteDream(dream.id)">彻底删除</button>
                </div>
              </article>
            </div>
          </div>
        </template>
      </div>
    </section>
  </main>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import api from './api'

const stage = ref('cover')
const user = ref(JSON.parse(localStorage.getItem('dream_user') || 'null'))
const view = ref('dreams')
const message = ref('')
const dreams = ref([])
const communityDreams = ref([])
const adminDreams = ref([])
const selected = ref(null)
const analysis = ref(null)

// 管理员模式开关状态
const isAdminMode = ref(false)

const today = new Date().toISOString().slice(0, 10)
const auth = reactive({ username: '', password: '' })
const form = reactive({
  title: '',
  content: '',
  dreamDate: today,
  moodScore: 3,
})

onMounted(() => { if (user.value) loadDreams() })
function enterApp() { stage.value = 'app' }

// 处理管理员开关切换事件
function handleAdminToggle() {
  if (isAdminMode.value) {
    auth.username = 'admin' // 自动填入管理员账号方便测试
    auth.password = ''
  } else {
    auth.username = ''
    auth.password = ''
  }
}

async function login() {
  const { data } = await api.post('/auth/login', auth)
  setUser(data)
  // 如果是管理员，登录后直接跳转到管理后台
  if (data.role === 'ADMIN') {
    openAdmin()
  }
}
async function register() {
  const { data } = await api.post('/auth/register', auth)
  setUser(data)
}
function setUser(data) {
  user.value = data
  localStorage.setItem('dream_user', JSON.stringify(data))
  localStorage.setItem('dream_token', data.token)
  message.value = isAdminMode.value ? '权限验证通过' : '登录成功'
  loadDreams()
}
function logout() {
  localStorage.removeItem('dream_user')
  localStorage.removeItem('dream_token')
  user.value = null
  selected.value = null
  analysis.value = null
  view.value = 'dreams' // 退出时重置视图
}
async function loadDreams() {
  const { data } = await api.get('/dreams')
  dreams.value = data
}
async function saveDream() {
  await api.post('/dreams', form)
  Object.assign(form, { title: '', content: '', dreamDate: today, moodScore: 3 })
  message.value = '碎片已封存'
  await loadDreams()
}
async function selectDream(dream) {
  selected.value = dream
  analysis.value = null
  try {
    const { data } = await api.get(`/dreams/${dream.id}/analysis`)
    analysis.value = data
  } catch { analysis.value = null }
}
async function analyzeDream(id) {
  const { data } = await api.post(`/dreams/${id}/analyze`)
  analysis.value = data
}
async function shareDream(id) {
  await api.post(`/dreams/${id}/share`)
  message.value = '已飘入匿名社区'
  await loadDreams()
}
async function openCommunity() {
  view.value = 'community'
  const { data } = await api.get('/community/dreams')
  communityDreams.value = data
}
async function openAdmin() {
  view.value = 'admin'
  const { data } = await api.get('/admin/community/dreams')
  adminDreams.value = data
}
async function hideDream(id) {
  await api.put(`/admin/community/dreams/${id}/hide`)
  await openAdmin()
}
async function deleteDream(id) {
  await api.delete(`/admin/community/dreams/${id}`)
  await openAdmin()
}
function formatJson(value) {
  try { return JSON.stringify(JSON.parse(value), null, 2) } catch { return value }
}
</script>