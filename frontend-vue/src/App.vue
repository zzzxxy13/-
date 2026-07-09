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
            <h3>梦境记录馆</h3>
            <p class="slogan">记录每一段睡梦，给夜里的碎片留一条可见的轨迹。</p>
            <button class="custom-enter-btn" @click="enterApp">ENTER</button>
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
          <h1 class="sidebar-title">梦境记录馆</h1>
        </div>

        <section v-if="user" class="user-box glass-panel sidebar-content-bottom">
          <span class="username">{{ user.username }}</span>
          <small class="role-tag">{{ user.role }}</small>
          <button class="danger logout-btn" @click="logout">退出</button>
        </section>
      </aside>

      <section class="workspace">
        <div v-if="!user" class="glass-panel login-panel fade-in">
          <div class="panel-header">
            <p class="eyebrow">{{ isAdminMode ? 'Admin Portal' : 'Sign In' }}</p>
            <h2>{{ isAdminMode ? '管理员入口' : '欢迎回来' }}</h2>
            <div class="title-line"></div>
          </div>
          <div class="form-grid">
            <div class="input-wrapper">
              <input v-model="auth.username" placeholder="用户名" />
              <span class="focus-border"></span>
            </div>
            <div class="input-wrapper">
              <input v-model="auth.password" type="password" placeholder="密码" @keyup.enter="login" />
              <span class="focus-border"></span>
            </div>

            <div class="admin-toggle-wrapper">
              <label class="admin-toggle">
                <input type="checkbox" v-model="isAdminMode" @change="handleAdminToggle" />
                <span class="toggle-slider"></span>
                <span class="toggle-label">管理员模式</span>
              </label>
            </div>

            <div class="actions" style="margin-top: 10px;">
              <button class="primary" @click="login">{{ isAdminMode ? '管理员登录' : '登录' }}</button>
              <button v-if="!isAdminMode" class="secondary" @click="register">注册</button>
            </div>
          </div>
          <p class="hint-message" :class="{ 'error-shake': isError }">{{ message }}</p>
        </div>

        <template v-else>
          <div class="top-nav">
            <button :class="{ active: view === 'dreams' }" @click="view = 'dreams'">我的梦境</button>
            <button :class="{ active: view === 'community' }" @click="openCommunity">社区广场</button>
            <button v-if="user?.role === 'ADMIN'" :class="{ active: view === 'admin' }" @click="openAdmin">管理后台</button>
          </div>

          <section v-if="view === 'dreams'" class="two-column dream-page-wrap fade-in">
            <div class="glass-panel compose dream-card">
              <p class="eyebrow">Record</p>
              <h2>记录梦境</h2>
              <div class="form-grid">
                <input v-model="form.title" placeholder="标题（如：教室追逐梦）" class="system-input" />
                <textarea v-model="form.content" placeholder="输入梦境内容..." class="system-textarea"></textarea>
                <div class="row">
                  <input v-model="form.dreamDate" type="date" class="system-date" />
                  <select v-model.number="form.moodScore" class="system-select">
                    <option :value="5">😊 心情很平稳</option>
                    <option :value="4">🙂 还不错</option>
                    <option :value="3">😌 一般</option>
                    <option :value="2">😟 偏低</option>
                    <option :value="1">😢 低落</option>
                  </select>
                </div>
                <button class="primary" style="width: 100%; margin-top: 8px;" @click="saveDream">保存梦境</button>
              </div>
              <p class="hint-message">{{ message }}</p>
            </div>

            <div class="glass-panel list dream-card">
              <div class="section-title">
                <p class="eyebrow">Archive</p>
                <h2>我的梦境列表</h2>
              </div>
              <div class="dream-list-container">
                <article
                  v-for="dream in dreams"
                  :key="dream.id"
                  class="dream-item dream-item-hover"
                  @click="selectDream(dream)"
                >
                  <div class="item-text">
                    <h3>{{ dream.title }}</h3>
                    <p>{{ dream.content }}</p>
                  </div>
                  <span class="mood-tag">{{ moodText(dream.moodScore) }}</span>
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
                <button class="primary" :disabled="analysisRunning" @click="analyzeDream(selected.id)">
                  {{ analysisRunning ? '分析中...' : '深度分析梦境' }}
                </button>
                <button class="secondary" @click="shareDream(selected.id, true)">匿名分享</button>
                <button class="secondary" @click="shareDream(selected.id, false)">实名分享</button>
                <button class="danger" @click="deleteSingleDream(selected.id)">删除记录</button>
              </div>
              <div v-if="analysisRunning" class="analysis-status-bar">
                <div class="analysis-status-text">{{ analysisStatusMessage }}</div>
                <div class="analysis-status-track">
                  <div class="analysis-status-progress" :style="{ width: `${analysisStatusProgress}%` }"></div>
                </div>
              </div>

              <section v-if="analysis" class="analysis-box">
                <p class="keyword-highlight">关键词提取：{{ analysis.matchedKeywords || '暂无' }}</p>
                <p class="analysis-text analysis-ai-subtitle">系统解析</p>
                <div class="analysis-text" v-html="escapeToHtml(analysis.ruleBasedResult)"></div>
                <p class="analysis-text analysis-ai-subtitle">AI 解析</p>
                <div class="analysis-text">
                  <section v-for="(sec, idx) in parsedAiSections" :key="`s-${idx}`" class="analysis-section">
                    <h3>{{ sec.title }}</h3>
                    <p v-for="(line, lidx) in sec.lines" :key="`l-${idx}-${lidx}`">{{ line }}</p>
                  </section>
                </div>
              </section>
            </div>
          </section>

          <section v-if="view === 'community'" class="community-wrap fade-in">
            <div class="section-title">
              <p class="eyebrow">COMMUNITY</p>
              <h2>社区广场</h2>
            </div>
            <div class="community-list">
              <article
                v-for="dream in communityDreams"
                :key="dream.id"
                class="community-bubble"
                :class="{ 'real-share': dream.isAnonymous === false, 'anon-share': dream.isAnonymous === true }"
              >
                <div class="bubble-top">
                  <span class="nick">{{ dream.isAnonymous ? '匿名用户' : (dream.username || `用户ID:${dream.ownerId}`) }}</span>
                  <h3>{{ dream.title }}</h3>
                </div>
                <div class="bubble-content"><p>{{ dream.content }}</p></div>

                <div class="interaction-bar">
                  <button class="icon-btn" @click="likeDream(dream)" :class="{ liked: dream.isLiked }">
                    <span>👍</span> 赞 ({{ dream.likes || 0 }})
                  </button>
                  <button class="icon-btn" @click="dream.showComments = !dream.showComments">
                    <span>💬</span> 评论 ({{ dream.commentCount || (dream.comments ? dream.comments.length : 0) }})
                  </button>
                  <span class="mood-tag" style="margin-left: auto;">{{ moodText(dream.moodScore) }}</span>
                </div>

                <div v-if="dream.showComments" class="comments-section fade-in">
                  <div class="comments-list" v-if="dream.comments.length > 0">
                    <div v-for="comment in dream.comments" :key="comment.id" class="comment-item">
                      <div class="comment-body">
                        <span class="comment-author">{{ comment.username }}:</span>
                        <span class="comment-text">{{ comment.content }}</span>
                      </div>
                      <button
                        v-if="user?.role === 'ADMIN'"
                        class="danger micro-btn"
                        @click="deleteComment(dream, comment.id)"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                  <div v-else class="empty-comments">还没有评论，来点亮第一条吧。</div>

                  <div class="comment-input-area">
                    <input
                      v-model="dream.newComment"
                      placeholder="写下你的评论..."
                      class="system-input comment-input"
                      @keyup.enter="submitComment(dream)"
                    />
                    <button class="primary comment-send-btn" @click="submitComment(dream)">发送</button>
                  </div>
                </div>
              </article>
            </div>
          </section>

          <section v-if="view === 'admin'" class="list wide fade-in">
            <div class="glass-panel">
              <div class="section-title">
                <p class="eyebrow">Admin</p>
                <h2>社区内容审核</h2>
              </div>
              <div class="dream-list-container">
                <article v-for="dream in adminDreams" :key="dream.id" class="dream-item">
                  <div class="item-text">
                    <h3>{{ dream.isAnonymous ? '匿名' : (dream.username || (`用户ID:${dream.ownerId}`)) }} / {{ dream.title }}</h3>
                    <p>{{ dream.content }}</p>
                    <small class="admin-status">状态：{{ dream.auditStatus }} | 点赞：{{ dream.likes || 0 }}</small>
                  </div>
                  <div class="actions">
                    <button class="secondary" @click="hideDream(dream.id)">下线</button>
                    <button class="danger" @click="deleteDream(dream.id)">删除</button>
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
import { computed, onMounted, reactive, ref } from 'vue'
import api from './api'

const stage = ref('cover')
const user = ref(JSON.parse(localStorage.getItem('dream_user') || 'null'))
const view = ref('dreams')
const message = ref('')
const isError = ref(false)
const isAdminMode = ref(false)

const dreams = ref([])
const communityDreams = ref([])
const adminDreams = ref([])
const selected = ref(null)
const analysis = ref(null)
const analysisRunning = ref(false)
const analysisStatusMessage = ref('')
const analysisStatusProgress = ref(0)

const isShareBusy = ref(false)

const auth = reactive({ username: '', password: '' })
const form = reactive({
  title: '',
  content: '',
  dreamDate: new Date().toISOString().slice(0, 10),
  moodScore: 3,
})

const parsedAiSections = computed(() => {
  const raw = analysis.value?.aiResult || ''
  if (!raw) return []

  const lines = raw.split('\n')
  const sections = []
  let current = null

  for (const l of lines) {
    const line = l.trim()
    if (!line) continue
    if (/^(关键词提取|意象语义解读|心理参考|情绪调适建议)[:：]/.test(line)) {
      if (current) sections.push(current)
      current = { title: line.replace(/[:：].*/, (m) => m), lines: [] }
      continue
    }
    if (!current) {
      current = { title: 'AI解析', lines: [] }
    }
    current.lines.push(line.replace(/^[-*·]\s*/, ''))
  }
  if (current) sections.push(current)
  if (sections.length === 0) {
    return [{ title: 'AI解析', lines: [raw] }]
  }
  return sections
})

const moodText = (score) => {
  if (score >= 5) return '😊'
  if (score === 4) return '🙂'
  if (score === 3) return '😌'
  if (score === 2) return '😟'
  return '😢'
}

const escapeToHtml = (text) => (text || '').replace(/\n/g, '<br/>')

onMounted(() => {
  if (user.value) {
    loadDreams()
  }
})

function enterApp() {
  stage.value = 'app'
}

function handleAdminToggle() {
  auth.username = isAdminMode.value ? 'admin' : ''
  auth.password = ''
  message.value = ''
  isError.value = false
}

function showMessage(text, isErr = false) {
  message.value = text
  isError.value = isErr
  if (!isErr) return
  setTimeout(() => {
    isError.value = false
  }, 1800)
}

function setUser(data) {
  user.value = data
  localStorage.setItem('dream_user', JSON.stringify(data))
  localStorage.setItem('dream_token', data.token)
  message.value = isAdminMode.value ? '管理员登录成功' : '登录成功'
  isError.value = false
  loadDreams()
}

async function login() {
  if (!auth.username || !auth.password) return showMessage('请输入用户名和密码', true)
  try {
    const { data } = await api.post('/auth/login', auth)
    setUser(data)
    if (data.role === 'ADMIN') {
      view.value = 'admin'
      await openAdmin()
    }
  } catch (err) {
    showMessage('登录失败：' + extractError(err), true)
  }
}

async function register() {
  if (!auth.username || !auth.password) return showMessage('请输入用户名和密码', true)
  try {
    const { data } = await api.post('/auth/register', auth)
    setUser(data)
  } catch (err) {
    showMessage('注册失败：' + extractError(err), true)
  }
}

function extractError(err) {
  const detail = err?.response?.data?.detail
  const msg = err?.message || ''
  if (detail) return detail
  if (msg) return msg
  return '请稍后重试'
}

function logout() {
  localStorage.removeItem('dream_user')
  localStorage.removeItem('dream_token')
  user.value = null
  selected.value = null
  analysis.value = null
  view.value = 'dreams'
  stage.value = 'cover'
}

async function loadDreams() {
  const { data } = await api.get('/dreams')
  dreams.value = data
}

async function saveDream() {
  if (!form.title.trim()) return showMessage('标题不能为空', true)
  if (!form.content.trim()) return showMessage('内容不能为空', true)
  await api.post('/dreams', { ...form })
  Object.assign(form, {
    title: '',
    content: '',
    dreamDate: new Date().toISOString().slice(0, 10),
    moodScore: 3,
  })
  showMessage('保存成功', false)
  await loadDreams()
}

async function selectDream(dream) {
  selected.value = dream
  analysis.value = null
  try {
    const { data } = await api.get(`/dreams/${dream.id}/analysis`)
    analysis.value = data
  } catch {
    analysis.value = null
  }
}

async function analyzeDream(id) {
  analysisRunning.value = true
  analysisStatusMessage.value = '正在提取关键词与生成分析...'
  analysisStatusProgress.value = 12
  try {
    const { data } = await api.post(`/dreams/${id}/analyze`)
    analysis.value = data
    analysisStatusMessage.value = '解析完成'
    analysisStatusProgress.value = 100
  } catch (err) {
    showMessage('分析失败：' + extractError(err), true)
  } finally {
    setTimeout(() => {
      analysisRunning.value = false
      analysisStatusMessage.value = ''
      analysisStatusProgress.value = 0
    }, 700)
  }
}

async function shareDream(id, isAnonymous) {
  if (isShareBusy.value) return
  isShareBusy.value = true
  try {
    const { data } = await api.post(`/dreams/${id}/share`, { isAnonymous })
    const type = isAnonymous ? '匿名' : '实名'
    const status = data.auditStatus || 'PUBLISHED'
    if (status === 'PENDING') {
      showMessage('投稿已提交，等待管理员审核')
    } else {
      showMessage(`已${type}分享到社区`)
    }
    await loadDreams()
    await openCommunity()
  } catch (err) {
    showMessage(`分享失败：${extractError(err)}（code=${err?.response?.status || '网络异常'}）`, true)
  } finally {
    isShareBusy.value = false
  }
}

async function deleteSingleDream(id) {
  if (!confirm('确认要删除该条梦境吗？')) return
  await api.delete(`/dreams/${id}`)
  selected.value = null
  analysis.value = null
  await loadDreams()
}

function normalizeDreamForCommunity(dream) {
  return {
    ...dream,
    comments: [],
    commentCount: dream.comments || dream.commentCount || 0,
    showComments: false,
    newComment: '',
    isLiked: !!dream.isLiked,
    isAnonymous: !!dream.isAnonymous,
  }
}

async function openCommunity() {
  view.value = 'community'
  try {
    const { data } = await api.get('/community/dreams')
    const enriched = await Promise.all(
      data.map(async (d) => {
        const normalized = normalizeDreamForCommunity(d)
        try {
          const commentsRes = await api.get(`/community/dreams/${d.id}/comments`)
          normalized.comments = commentsRes.data || []
          normalized.commentCount = normalized.comments.length
        } catch {
          normalized.comments = []
        }
        return normalized
      }),
    )
    communityDreams.value = enriched
  } catch (err) {
    communityDreams.value = []
    showMessage('社区加载失败：' + extractError(err), true)
  }
}

async function likeDream(dream) {
  const next = !dream.isLiked
  const { data } = await api.post(`/community/dreams/${dream.id}/like`, { isLiked: next })
  dream.isLiked = data.isLiked
  dream.likes = data.likes
}

async function loadCommunityComments(dream) {
  const commentsRes = await api.get(`/community/dreams/${dream.id}/comments`)
  dream.comments = commentsRes.data || []
  dream.commentCount = dream.comments.length
}

async function submitComment(dream) {
  const content = (dream.newComment || '').trim()
  if (!content) return
  await api.post(`/community/dreams/${dream.id}/comments`, { content })
  dream.newComment = ''
  await loadCommunityComments(dream)
}

async function deleteComment(dream, commentId) {
  if (!confirm('确认删除该评论吗？')) return
  await api.delete(`/admin/comments/${commentId}`)
  await loadCommunityComments(dream)
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
</script>
