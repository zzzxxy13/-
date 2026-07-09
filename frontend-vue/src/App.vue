<template>
  <main class="dream-app">
    
    <div class="video-bg-container">
      <video autoplay loop muted playsinline class="dynamic-video">
        <source src="/dynamic-bg.mp4" type="video/mp4" />
      </video>
      <div class="video-overlay" :class="{ 'app-mode-overlay': stage === 'app' }"></div>
    </div>

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

    <section v-else class="app-core app-shell fade-in">
      
      <aside class="sidebar">
        <div class="sidebar-bg-container">
          <video autoplay loop muted playsinline class="sidebar-video">
            <source src="/dynamic-bg.mp4" type="video/mp4" />
          </video>
          <div class="sidebar-overlay"></div>
        </div>

        <div class="sidebar-content-top">
          <p class="eyebrow">Dream Archive</p>
          <h1 class="sidebar-title">藏梦馆</h1>
        </div>
        
        <section v-if="user" class="user-box glass-panel sidebar-content-bottom">
          <span class="username">{{ user.username }}</span>
          <small class="role-tag">{{ user.role }}</small>
          <button class="danger logout-btn" @click="logout">退出</button>
        </section>
      </aside>

      <section class="workspace">
        
        <div v-if="user" class="top-nav">
          <button :class="{ active: view === 'dreams' }" @click="view = 'dreams'">我的梦境</button>
          <button :class="{ active: view === 'community' }" @click="openCommunity">幻夜社区</button>
          <button v-if="user?.role === 'ADMIN'" :class="{ active: view === 'admin' }" @click="openAdmin">管理后台</button>
        </div>

        <div v-if="!user" class="glass-panel login-panel fade-in">
          <div class="panel-header">
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
              <input v-model="auth.password" type="password" placeholder="请输入密码 (新用户请点击注册)" @keyup.enter="login" />
              <span class="focus-border"></span>
            </div>
            
            <div class="admin-toggle-wrapper">
              <label class="admin-toggle">
                <input type="checkbox" v-model="isAdminMode" @change="handleAdminToggle" />
                <span class="toggle-slider"></span>
                <span class="toggle-label">启用管理员通道</span>
              </label>
            </div>

            <div class="actions" style="margin-top: 10px;">
              <button class="primary" @click="login">{{ isAdminMode ? '验证权限' : '登录幻夜' }}</button>
              <button v-if="!isAdminMode" class="secondary" @click="register">注册档案</button>
            </div>
          </div>
          <p class="hint-message" :class="{'error-shake': isError}">{{ message }}</p>
        </div>

        <template v-else>
          <section v-if="view === 'dreams'" class="two-column dream-page-wrap fade-in">
            <div class="glass-panel compose dream-card">
              <p class="eyebrow">Record</p>
              <h2>记录新的梦</h2>
              <div class="form-grid">
                <input v-model="form.title" placeholder="梦境标题" class="system-input" />
                <textarea v-model="form.content" placeholder="写下梦里最清晰的片段" class="system-textarea"></textarea>
                <div class="row">
                  <input v-model="form.dreamDate" type="date" class="system-date" />
                  <select v-model="form.moodScore" class="system-select">
                    <option value="positive">😊 积极愉快</option>
                    <option value="neutral">😐 中性平静</option>
                    <option value="negative">😢 悲伤负面</option>
                  </select>
                </div>
                <button class="primary" style="width: 100%; margin-top: 10px;" @click="saveDream">保存梦境</button>
              </div>
              <p class="hint-message">{{ message }}</p>
            </div>

            <div class="glass-panel list dream-card">
              <div class="section-title">
                <p class="eyebrow">Archive</p>
                <h2>我的梦境列表</h2>
              </div>
              <div class="dream-list-container">
                <article v-for="dream in dreams" :key="dream.id" class="dream-item dream-item-hover" @click="selectDream(dream)">
                  <div class="item-text">
                    <h3>{{ dream.title }}</h3>
                    <p>{{ dream.content }}</p>
                  </div>
                  <span class="mood-tag">{{ dream.moodScore >=4 ? '😊' : dream.moodScore ===3 ? '😐' : '😢' }}</span>
                </article>
              </div>
            </div>

            <div v-if="selected" class="glass-panel detail dream-card fade-in">
              <div class="section-title">
                <p class="eyebrow">Analysis</p>
                <h2>{{ selected.title }}</h2>
              </div>
              <p class="detail-content">{{ selected.content }}</p>
              <div class="actions">
                <button class="primary" @click="analyzeDream(selected.id)">深度分析梦境</button>
                <button class="secondary" @click="shareDreamRealName(selected.id)">实名分享</button>
                <button class="secondary" @click="shareDream(selected.id)">匿名分享</button>
                <button class="danger" @click="deleteSingleDream(selected.id)">删除梦境</button>
              </div>
              <section v-if="analysis" class="analysis-box">
                <strong class="keyword-highlight">命中关键词：{{ analysis.matchedKeywords || '暂无命中' }}</strong>
                <p class="analysis-text">{{ analysis.ruleBasedResult }}</p>
                <pre>{{ formatJson(analysis.aiResult) }}</pre>
              </section>
            </div>
          </section>

          <section v-if="view === 'community'" class="community-wrap fade-in">
            <div class="section-title">
              <p class="eyebrow">COMMUNITY</p>
              <h2>幻夜社区</h2>
            </div>
            <div class="community-list">
              <article v-for="dream in communityDreams" :key="dream.id" class="community-bubble" :class="{ 'real-share': dream.isAnonymous === false, 'anon-share': dream.isAnonymous === true }">
                <div class="bubble-top">
                  <span class="nick">
                    <template v-if="dream.isAnonymous">匿名用户</template>
                    <template v-else>{{ dream.username || `用户 ID: ${dream.ownerId}` }}</template>
                  </span>
                  <h3>· {{ dream.title }}</h3>
                </div>
                <div class="bubble-content">
                  <p>{{ dream.content }}</p>
                </div>
                
                <div class="interaction-bar">
                  <button class="icon-btn" @click="likeDream(dream)" :class="{ 'liked': dream.isLiked }">
                    <span class="icon">✨</span> 共鸣 ({{ dream.likes || 0 }})
                  </button>
                  <button class="icon-btn" @click="dream.showComments = !dream.showComments">
                    <span class="icon">💬</span> 留言 ({{ dream.comments?.length || 0 }})
                  </button>
                  <span class="mood-tag" style="margin-left: auto;">
                    {{ dream.moodScore >=4 ? '😊' : dream.moodScore ===3 ? '😐' : '😢' }}
                  </span>
                </div>

                <div v-if="dream.showComments" class="comments-section fade-in">
                  <div class="comments-list" v-if="dream.comments && dream.comments.length > 0">
                    <div v-for="comment in dream.comments" :key="comment.id" class="comment-item">
                      <div class="comment-body">
                        <span class="comment-author">{{ comment.username }}:</span>
                        <span class="comment-text">{{ comment.content }}</span>
                      </div>
                      <button v-if="user?.role === 'ADMIN'" class="danger micro-btn" @click="deleteComment(dream, comment.id)">删除</button>
                    </div>
                  </div>
                  <div v-else class="empty-comments">还没有灵魂留下回响...</div>
                  
                  <div class="comment-input-area">
                    <input v-model="dream.newComment" placeholder="写下你的感受..." class="system-input comment-input" @keyup.enter="submitComment(dream)" />
                    <button class="primary comment-send-btn" @click="submitComment(dream)">发送</button>
                  </div>
                </div>

                <div class="bubble-bottom" v-if="dream.ownerId === user.id">
                  <button 
                    class="secondary revoke-btn" 
                    @click.stop="hideFromCommunity(dream.id)" 
                    style="margin-left: auto; border-color: rgba(255,255,255,0.3); color: #cbd5ef;"
                  >
                    👁️ 在社区隐藏
                  </button>
                </div>
              </article>
            </div>
          </section>

          <section v-if="view === 'admin'" class="list wide fade-in">
            <div class="glass-panel">
              <div class="section-title">
                <p class="eyebrow">Admin</p>
                <h2>社区内容监管</h2>
              </div>
              <div class="dream-list-container">
                <article v-for="dream in adminDreams" :key="dream.id" class="dream-item">
                  <div class="item-text">
                    <h3>{{ dream.isAnonymous ? '匿名' : (dream.username || `用户 ID:${dream.ownerId}`) }} · {{ dream.title }}</h3>
                    <p>{{ dream.content }}</p>
                    <small class="admin-status">当前状态：{{ dream.auditStatus }} | 共鸣数: {{ dream.likes || 0 }}</small>
                  </div>
                  <div class="actions">
                    <button class="secondary" @click="hideDream(dream.id)">下架违规内容</button>
                    <button class="danger" @click="deleteDream(dream.id)">彻底删除记录</button>
                  </div>
                </article>
              </div>
            </div>
          </section>
        </template>
      </section>
    </section>
  </main>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import api from './api'

// UI 与 视图状态
const stage = ref('cover')
const user = ref(JSON.parse(localStorage.getItem('dream_user') || 'null'))
const view = ref('dreams')
const message = ref('')
const isError = ref(false) 
const isAdminMode = ref(false)

// 数据集
const dreams = ref([])
const communityDreams = ref([])
const adminDreams = ref([])
const selected = ref(null)
const analysis = ref(null)
const today = new Date().toISOString().slice(0, 10)

const auth = reactive({ username: '', password: '' })
const form = reactive({ title: '', content: '', dreamDate: today, moodScore: 'neutral' })

onMounted(() => { if (user.value) loadDreams() })
function enterApp() { stage.value = 'app' }

function handleAdminToggle() {
  auth.username = isAdminMode.value ? 'admin' : ''
  auth.password = ''
  message.value = ''
  isError.value = false
}

function showError(msg) {
  message.value = msg;
  isError.value = true;
  setTimeout(() => isError.value = false, 500);
}

// 登录模块：精准区分密码错、未注册状态
async function login() {
  if (!auth.username || !auth.password) return showError("请输入用户名和密码"); 
  try {
    const { data } = await api.post('/auth/login', auth)
    setUser(data)
    if (data.role === 'ADMIN') openAdmin()
  } catch (err) {
    const status = err.response?.status;
    const errorMsg = (err.response?.data?.msg || err.response?.data?.detail || '').toLowerCase();
    
    if (status === 404 || errorMsg.includes('not found') || errorMsg.includes('不存在') || errorMsg.includes('未注册')) {
      showError('账号未注册，请先点击下方的"注册档案"');
    } else if (status === 401 || errorMsg.includes('password') || errorMsg.includes('密码') || errorMsg.includes('错误')) {
      showError('密码错误，请重新输入');
    } else {
      showError('账号未注册或密码错误，新用户请先注册');
    }
  }
}

async function register() {
  if (!auth.username || !auth.password) return showError("请填写用户名和密码进行注册"); 
  try {
    const { data } = await api.post('/auth/register', auth)
    setUser(data)
  } catch (err) {
    showError('注册失败：' + (err.response?.data?.msg || '用户名可能已存在'));
  }
}

function setUser(data) {
  user.value = data
  localStorage.setItem('dream_user', JSON.stringify(data))
  localStorage.setItem('dream_token', data.token)
  message.value = isAdminMode.value ? '权限验证通过' : '登录成功'
  isError.value = false
  loadDreams()
}

// 退出重置
function logout() {
  localStorage.removeItem('dream_user')
  localStorage.removeItem('dream_token')
  user.value = null; selected.value = null; analysis.value = null;
  view.value = 'dreams'; stage.value = 'cover' 
}

// 个人藏梦逻辑
async function loadDreams() { const { data } = await api.get('/dreams'); dreams.value = data }
async function saveDream() {
  try {
    if (!form.title.trim()) return showError('请填写梦境标题')
    if (!form.content.trim()) return showError('请填写梦境内容')
    const moodMap = { positive: 5, neutral: 3, negative: 1 }
    await api.post('/dreams', { ...form, moodScore: moodMap[form.moodScore] })
    Object.assign(form, { title: '', content: '', dreamDate: today, moodScore: 'neutral' })
    message.value = '梦境保存成功！'; isError.value = false;
    await loadDreams()
  } catch (err) { showError('保存失败') }
}

async function selectDream(dream) {
  selected.value = dream; analysis.value = null;
  try { const { data } = await api.get(`/dreams/${dream.id}/analysis`); analysis.value = data } catch {}
}
async function analyzeDream(id) { const { data } = await api.post(`/dreams/${id}/analyze`); analysis.value = data }
async function shareDream(id) { await api.post(`/dreams/${id}/share`, { isAnonymous: true }); message.value = '已提交匿名分享'; await loadDreams() }
async function shareDreamRealName(id) { await api.post(`/dreams/${id}/share`, { isAnonymous: false }); message.value = '已提交实名分享'; await loadDreams() }
async function deleteSingleDream(id) {
  if (!confirm('确定彻底删除这条记录吗？')) return;
  try { await api.delete(`/dreams/${id}`); selected.value = null; await loadDreams() } catch {}
}

// 幻夜社区业务
async function openCommunity() {
  view.value = 'community'
  const { data } = await api.get('/community/dreams')
  communityDreams.value = data.map(d => ({ ...d, showComments: false, newComment: '' }))
}

// 核心改动：仅在社区隐藏（修改 is_shared 状态），不破坏原始记录
async function hideFromCommunity(id) {
  if (!confirm('确定要在社区隐藏这条梦境吗？隐藏后它将只保留在你的【我的梦境】列表中。')) return
  try {
    await api.delete(`/community/dreams/${id}`) 
    await openCommunity()
    await loadDreams() 
    message.value = '已成功从社区隐藏'
  } catch (err) {
    showError('操作失败')
  }
}

// 乐观交互：共鸣点赞
async function likeDream(dream) {
  dream.isLiked = !dream.isLiked
  dream.likes = (dream.likes || 0) + (dream.isLiked ? 1 : -1)
  try {
    await api.post(`/community/dreams/${dream.id}/like`, { isLiked: dream.isLiked })
  } catch (err) { console.warn('演示模式：后端点赞接口未连通') }
}

// 乐观交互：发布评论
async function submitComment(dream) {
  const content = dream.newComment?.trim()
  if (!content) return
  
  const fakeComment = {
    id: Date.now(), 
    username: user.value.username || '当前用户',
    content: content
  }
  if (!dream.comments) dream.comments = []
  dream.comments.push(fakeComment)
  dream.newComment = '' 

  try {
    const { data } = await api.post(`/community/dreams/${dream.id}/comments`, { content })
    Object.assign(fakeComment, data)
  } catch (err) { console.warn('演示模式：后端评论接口未连通') }
}

async function deleteComment(dream, commentId) {
  if (!confirm('确定要删除这条违规评论吗？')) return
  dream.comments = dream.comments.filter(c => c.id !== commentId)
  try { await api.delete(`/admin/comments/${commentId}`) } catch (err) {}
}

// 监管后台
async function openAdmin() { view.value = 'admin'; const { data } = await api.get('/admin/community/dreams'); adminDreams.value = data }
async function hideDream(id) { await api.put(`/admin/community/dreams/${id}/hide`); await openAdmin() }
async function deleteDream(id) { await api.delete(`/admin/community/dreams/${id}`); await openAdmin() }
function formatJson(value) { try { return JSON.stringify(JSON.parse(value), null, 2) } catch { return value } }
</script>