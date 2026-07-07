<template>
  <main class="app-shell">
    <aside class="sidebar">
      <div>
        <p class="eyebrow">Dream Archive</p>
        <h1>梦境馆</h1>
      </div>
      <nav>
        <button :class="{ active: view === 'dreams' }" @click="view = 'dreams'">我的梦境</button>
        <button :class="{ active: view === 'community' }" @click="openCommunity">匿名社区</button>
        <button v-if="user?.role === 'ADMIN'" :class="{ active: view === 'admin' }" @click="openAdmin">管理后台</button>
      </nav>
      <section v-if="user" class="user-box">
        <span>{{ user.username }}</span>
        <small>{{ user.role }}</small>
        <button @click="logout">退出</button>
      </section>
    </aside>

    <section class="workspace">
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
        <section v-if="view === 'dreams'" class="two-column">
          <div class="compose">
            <p class="eyebrow">Record</p>
            <h2>记录新的梦</h2>
            <input v-model="form.title" placeholder="梦境标题" />
            <textarea v-model="form.content" placeholder="写下梦里最清晰的片段"></textarea>
            <div class="row">
              <input v-model="form.dreamDate" type="date" />
              <select v-model.number="form.moodScore">
                <option :value="1">1 星 强烈负面</option>
                <option :value="2">2 星 偏负面</option>
                <option :value="3">3 星 中性</option>
                <option :value="4">4 星 偏正面</option>
                <option :value="5">5 星 积极愉快</option>
              </select>
            </div>
            <button class="primary" @click="saveDream">保存梦境</button>
            <p class="hint">{{ message }}</p>
          </div>

          <div class="list">
            <div class="section-title">
              <p class="eyebrow">Archive</p>
              <h2>我的梦境</h2>
            </div>
            <article v-for="dream in dreams" :key="dream.id" class="dream-item" @click="selectDream(dream)">
              <div>
                <h3>{{ dream.title }}</h3>
                <p>{{ dream.content }}</p>
              </div>
              <span>{{ dream.moodScore }} 星</span>
            </article>
          </div>

          <div v-if="selected" class="detail">
            <div class="section-title">
              <p class="eyebrow">Analysis</p>
              <h2>{{ selected.title }}</h2>
            </div>
            <p>{{ selected.content }}</p>
            <div class="actions">
              <button class="primary" @click="analyzeDream(selected.id)">分析梦境</button>
              <button @click="shareDream(selected.id)">匿名分享</button>
            </div>
            <section v-if="analysis" class="analysis">
              <strong>关键词：{{ analysis.matchedKeywords || '暂无命中' }}</strong>
              <p>{{ analysis.ruleBasedResult }}</p>
              <pre>{{ formatJson(analysis.aiResult) }}</pre>
            </section>
          </div>
        </section>

        <section v-if="view === 'community'" class="list wide">
          <div class="section-title">
            <p class="eyebrow">Community</p>
            <h2>匿名梦境社区</h2>
          </div>
          <article v-for="dream in communityDreams" :key="dream.id" class="dream-item">
            <div>
              <h3>{{ dream.anonymousName }} · {{ dream.title }}</h3>
              <p>{{ dream.content }}</p>
            </div>
            <span>{{ dream.moodScore }} 星</span>
          </article>
        </section>

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
  moodScore: 3,
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
  await api.post('/dreams', form)
  Object.assign(form, { title: '', content: '', dreamDate: today, moodScore: 3 })
  message.value = '梦境已保存'
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
  const { data } = await api.post(`/dreams/${id}/analyze`)
  analysis.value = data
}

async function shareDream(id) {
  await api.post(`/dreams/${id}/share`)
  message.value = '已提交匿名分享'
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
  try {
    return JSON.stringify(JSON.parse(value), null, 2)
  } catch {
    return value
  }
}
</script>

