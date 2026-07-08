<template>
  <main class="app-shell">
    <aside class="sidebar">
      <div>
        <p class="eyebrow">Dream Archive</p>
        <h1>梦境馆</h1>
      </div>
      <!-- 原侧边导航按钮全部移除，移到顶部workspace上方 -->
      <section v-if="user" class="user-box">
        <span>{{ user.username }}</span>
        <small>{{ user.role }}</small>
        <button @click="logout">退出</button>
      </section>
    </aside>
    <section class="workspace">
      <!-- 顶部横向导航栏 新增 -->
      <div class="top-nav">
        <button 
          :class="{ active: view === 'dreams' }" 
          @click="view = 'dreams'"
        >
          我的梦境
        </button>
        <button 
          :class="{ active: view === 'community' }" 
          @click="openCommunity"
        >
          社区
        </button>
        <button 
          v-if="user?.role === 'ADMIN'" 
          :class="{ active: view === 'admin' }" 
          @click="openAdmin"
        >
          管理后台
        </button>
      </div>

      <!-- 登录面板 不变 -->
      <section v-if="!user" class="login-panel">
        <p class="eyebrow">Sign in</p>
        <h2>进入你的梦境档案</h2>
        <div class="form-grid">
          <input v-model="auth.username" placeholder="用户名，例如 alice / admin" />
          <input v-model="auth.password" type="password" placeholder="密码，例如 123456 / admin123" />
          <div class="actions">
            <button class="primary" @click="login">登录</button>
            <button @click="register">注册</button>
          </div>
        </div>
        <p class="hint">{{ message }}</p>
      </section>

      <template v-else>
        <!-- 【美化后的我的梦境板块】 -->
        <section v-if="view === 'dreams'" class="two-column dream-page-wrap">
          <!-- 左侧：新建梦境卡片 -->
          <div class="compose dream-card">
            <p class="eyebrow">Record</p>
            <h2>记录新的梦</h2>
            <input v-model="form.title" placeholder="梦境标题" />
            <textarea v-model="form.content" placeholder="写下梦里最清晰的片段"></textarea>
            <div class="row">
              <input v-model="form.dreamDate" type="date" />
              <select v-model="form.moodScore">
                <option value="positive">😊 </option>
                <option value="neutral">😐 </option>
                <option value="negative">😢 </option>
              </select>
            </div>
            <button class="primary" @click="saveDream">保存梦境</button>
            <p class="hint">{{ message }}</p>
          </div>

          <!-- 右侧：梦境列表卡片 -->
          <div class="list dream-card">
            <div class="section-title">
              <p class="eyebrow">Archive</p>
              <h2>我的梦境列表</h2>
            </div>
            <article 
              v-for="dream in dreams" 
              :key="dream.id" 
              class="dream-item dream-item-hover" 
              @click="selectDream(dream)"
            >
              <div>
                <h3>{{ dream.title }}</h3>
                <p>{{ dream.content }}</p>
              </div>
              <span class="mood-tag">
                {{ dream.moodScore >=4 ? '😊 ' : dream.moodScore ===3 ? '😐 ' : '😢 ' }}
              </span>
            </article>
          </div>

          <!-- 下方：梦境详情&AI分析卡片 -->
          <div v-if="selected" class="detail dream-card">
            <div class="section-title">
              <p class="eyebrow">Analysis</p>
              <h2>{{ selected.title }}</h2>
            </div>
            <p class="detail-content">{{ selected.content }}</p>
            <div class="actions">
              <button class="primary" @click="analyzeDream(selected.id)">分析梦境</button>
              <!-- 新增：实名分享按钮 -->
              <button @click="shareDreamRealName(selected.id)">实名分享</button>
              <!-- 原有匿名分享 -->
              <button @click="shareDream(selected.id)">匿名分享</button>
              <!-- 新增删除按钮 -->
              <button class="danger" @click="deleteSingleDream(selected.id)">删除梦境</button>
            </div>
            <section v-if="analysis" class="analysis">
              <strong>关键词：{{ analysis.matchedKeywords || '暂无命中' }}</strong>
              <p>{{ analysis.ruleBasedResult }}</p>
              <pre>{{ formatJson(analysis.aiResult) }}</pre>
            </section>
          </div>
        </section>

        <section v-if="view === 'community'" class="community-wrap">
          <div class="section-title">
            <p class="eyebrow">COMMUNITY</p>
            <h2>梦境社区</h2>
          </div>
          <div class="community-list">
            <article 
              v-for="dream in communityDreams" 
              :key="dream.id" 
              class="community-bubble"
              :class="{ 'real-share': dream.isAnonymous === false, 'anon-share': dream.isAnonymous === true }"
            >
              <div class="bubble-top">
                <span class="nick">
                  <template v-if="dream.isAnonymous">匿名用户</template>
                  <template v-else>{{ dream.username }}</template>
                </span>
                <h3>· {{ dream.title }}</h3>
              </div>
             <div class="bubble-content">
                <p>{{ dream.content }}</p>
              </div>
              <div class="bubble-bottom">
                <span class="mood-tag">
                  {{ dream.moodScore >=4 ? '😊 正面' : dream.moodScore ===3 ? '😐 中性' : '😢 负面' }}
                </span>
                <button 
                  v-if="dream.ownerId === user.id"
                  class="revoke-btn" 
                  @click.stop="deleteCommunityDream(dream.id)"
                >撤回分享</button>
              </div>
            </article>
          </div>
        </section>

        <!-- 管理后台 不变 -->
        <section v-if="view === 'admin'" class="list wide">
          <div class="section-title">
            <p class="eyebrow">Admin</p>
            <h2>社区内容监管</h2>
          </div>
          <article v-for="dream in adminDreams" :key="dream.id" class="dream-item">
            <div>
              <h3>{{ dream.anonymousName }} · {{ dream.title }}</h3>
              <p>{{ dream.content }}</p>
              <small>状态：{{ dream.auditStatus }}</small>
            </div>
            <div class="actions">
              <button @click="hideDream(dream.id)">下架</button>
              <button class="danger" @click="deleteDream(dream.id)">删除</button>
            </div>
          </article>
        </section>
      </template>
    </section>
  </main>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import api from './api'
const user = ref(JSON.parse(localStorage.getItem('dream_user') || 'null'))
const view = ref('dreams')
const message = ref('')
const dreams = ref([])
const communityDreams = ref([])
const adminDreams = ref([])
const selected = ref(null)
const analysis = ref(null)
const today = new Date().toISOString().slice(0, 10)
const auth = reactive({ username: 'alice', password: '123456' })
const form = reactive({
  title: '',
  content: '',
  dreamDate: today,
  moodScore: 'neutral',
})
onMounted(() => {
  if (user.value) {
    loadDreams()
  }
})
async function login() {
  const { data } = await api.post('/auth/login', auth)
  setUser(data)
}
async function register() {
  const { data } = await api.post('/auth/register', auth)
  setUser(data)
}
function setUser(data) {
  user.value = data
  localStorage.setItem('dream_user', JSON.stringify(data))
  localStorage.setItem('dream_token', data.token)
  message.value = '登录成功'
  loadDreams()
}
function logout() {
  localStorage.removeItem('dream_user')
  localStorage.removeItem('dream_token')
  user.value = null
  selected.value = null
  analysis.value = null
}
async function loadDreams() {
  const { data } = await api.get('/dreams')
  dreams.value = data
}
async function saveDream() {
  try {
    // 表单空值校验
    if (!form.title.trim()) {
      message.value = '请填写梦境标题'
      return
    }
    if (!form.content.trim()) {
      message.value = '请填写梦境内容'
      return
    }
    // 前端字符串情绪转后端需要的数字
    const moodMap = {
      positive: 5,
      neutral: 3,
      negative: 1
    }
    const submitData = {
      ...form,
      moodScore: moodMap[form.moodScore]
    }
    await api.post('/dreams', submitData)
    // 清空表单，恢复情绪默认中性
    Object.assign(form, {
      title: '',
      content: '',
      dreamDate: today,
      moodScore: 'neutral'
    })
    message.value = '梦境保存成功！'
    await loadDreams()
  } catch (err) {
    console.error('保存梦境出错', err)
    message.value = '保存失败：' + (err.response?.data?.msg || '后端未启动/参数错误')
  }
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
  const { data } = await api.post(`/dreams/${id}/analyze`)
  analysis.value = data
}
// 原有匿名分享
async function shareDream(id) {
  await api.post(`/dreams/${id}/share`, { isAnonymous: true })
  message.value = '已提交匿名分享'
  await loadDreams()
}
// 新增：实名分享函数
async function shareDreamRealName(id) {
  await api.post(`/dreams/${id}/share`, { isAnonymous: false })
  message.value = '已提交实名分享，将展示你的用户名'
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
// 删除单条个人梦境
async function deleteSingleDream(id) {
  // 弹窗确认防止误删
  const sure = confirm('确定要永久删除这条梦境记录吗？删除后无法恢复！')
  if (!sure) return
  try {
    await api.delete(`/dreams/${id}`)
    message.value = '梦境删除成功'
    // 清空当前选中详情
    selected.value = null
    analysis.value = null
    // 刷新梦境列表
    await loadDreams()
  } catch (err) {
    console.error('删除失败', err)
    message.value = '删除失败：'+(err.response?.data?.msg || '接口异常')
  }
}
// 删除自己发布到社区的分享梦境（只移除社区展示，不删除本地原始梦境）
async function deleteCommunityDream(id) {
  const sure = confirm('确定要撤回这条社区分享？私有梦境不会被删除！')
  if (!sure) return // 不点确定直接不发请求
  try {
    await api.delete(`/community/dreams/${id}`)
    message.value = '社区分享已撤回'
    await openCommunity() // 只刷新社区列表，不碰私人梦境
  } catch (err) {
    console.error('撤回分享失败', err)
    // 打印完整错误，看状态码
    message.value = '撤回失败：' + (err.response?.data?.msg || '接口不存在/无权限')
  }
}
async function deleteDream(id) {
  await api.delete(`/admin/community/dreams/${id}`)
  await openAdmin()
}
function formatJson(value) {
  try {
    return JSON.stringify(JSON.parse(value), null, 2)
  } catch {
    return value
  }
}
</script>
