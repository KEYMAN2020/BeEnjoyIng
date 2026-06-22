<template>
  <div class="chat-page">
    <!-- 顶部导航栏（微信风格） -->
    <div class="chat-header">
      <button class="back-btn" @click="$router.back()">
        <span class="back-arrow">‹</span>
      </button>
      <div class="header-title">
        <span class="group-name">{{ groupName }}</span>
        <span class="member-count" v-if="memberCount > 0">({{ memberCount }})</span>
      </div>
      <div class="header-right"></div>
    </div>

    <!-- 消息列表 -->
    <div class="chat-messages" ref="messagesEl">
      <div v-if="loading" class="loading-wrap">
        <div class="spinner"></div>
      </div>

      <template v-else>
        <div
          v-for="(msg, index) in messages"
          :key="msg.id"
        >
          <!-- 时间分隔线（同一分钟内不重复显示） -->
          <div class="msg-time-divider" v-if="showTimeDivider(msg, index)">
            {{ formatTimeFull(msg.created_at) }}
          </div>

          <!-- 消息行 -->
          <div class="msg-row" :class="isMine(msg) ? 'is-mine' : 'is-other'">
            <!-- 对方头像（左侧） -->
            <div class="msg-avatar" v-if="!isMine(msg)">
              <img
                v-if="msg.sender_avatar"
                :src="msg.sender_avatar"
                :alt="msg.sender_name"
                class="avatar-img"
              />
              <div v-else class="avatar-placeholder">
                {{ (msg.sender_name || '?').charAt(0) }}
              </div>
            </div>

            <!-- 消息内容区 -->
            <div class="msg-content">
              <!-- 对方昵称 -->
              <div class="msg-sender-name" v-if="!isMine(msg) && msg.sender_name">
                {{ msg.sender_name }}
              </div>
              <!-- 气泡 -->
              <div class="msg-bubble-wrap">
                <div class="msg-bubble" :class="isMine(msg) ? 'bubble-mine' : 'bubble-other'">
                  {{ msg.content }}
                </div>
              </div>
            </div>

            <!-- 自己头像（右侧） -->
            <div class="msg-avatar" v-if="isMine(msg)">
              <img
                v-if="myAvatar"
                :src="myAvatar"
                class="avatar-img"
                alt="我"
              />
              <div v-else class="avatar-placeholder avatar-mine">
                {{ myInitial }}
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div class="empty-chat" v-if="messages.length === 0">
          <p>暂无消息，来打个招呼吧 👋</p>
        </div>
      </template>

      <!-- 底部占位（防止被输入栏遮挡） -->
      <div style="height: 16px"></div>
    </div>

    <!-- 底部输入栏（微信风格） -->
    <div class="chat-input-bar">
      <div class="input-wrap">
        <textarea
          ref="inputEl"
          v-model="inputMsg"
          class="chat-input"
          placeholder="发消息..."
          rows="1"
          @keydown.enter.exact.prevent="sendMessage"
          @input="autoResize"
        ></textarea>
      </div>
      <button
        class="send-btn"
        :class="{ 'send-btn-active': inputMsg.trim() }"
        @click="sendMessage"
        :disabled="!inputMsg.trim() || sending"
      >
        发送
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { chatAPI } from '@/api'

const route = useRoute()
const auth = useAuthStore()

const groupName = ref('群聊')
const memberCount = ref(0)
const loading = ref(true)
const sending = ref(false)
const messages = ref([])
const inputMsg = ref('')
const messagesEl = ref(null)
const inputEl = ref(null)
const currentUserId = ref(null)
let pollTimer = null

const myAvatar = computed(() => auth.user?.avatar_url || auth.user?.avatar || null)
const myInitial = computed(() => {
  const name = auth.user?.nickname || auth.user?.username || '我'
  return name.charAt(0)
})

function isMine(msg) {
  return msg.sender_id === currentUserId.value
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function formatTimeFull(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  const isYesterday = d.toDateString() === yesterday.toDateString()

  const hhmm = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  if (isToday) return hhmm
  if (isYesterday) return `昨天 ${hhmm}`
  const month = d.getMonth() + 1
  const day = d.getDate()
  return `${month}月${day}日 ${hhmm}`
}

function showTimeDivider(msg, index) {
  if (index === 0) return true
  const prev = messages.value[index - 1]
  if (!prev) return true
  const curr = new Date(msg.created_at)
  const prevTime = new Date(prev.created_at)
  // 相差超过 5 分钟就显示时间
  return (curr - prevTime) > 5 * 60 * 1000
}

function scrollToBottom(smooth = false) {
  nextTick(() => {
    const el = messagesEl.value
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: smooth ? 'smooth' : 'auto' })
    }
  })
}

function autoResize() {
  const el = inputEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 100) + 'px'
}

async function loadMessages() {
  try {
    const res = await chatAPI.messages(route.params.groupId)
    if (res.data.code === 0) {
      const d = res.data.data
      const newMsgs = d.messages || d || []
      currentUserId.value = auth.user?.id
      groupName.value = d?.group_name || d?.group?.name || '群聊'
      memberCount.value = d?.member_count || d?.group?.member_count || 0

      const prevLen = messages.value.length
      messages.value = newMsgs

      // 只有新消息时才滚动
      if (newMsgs.length > prevLen) scrollToBottom(prevLen > 0)
    }
  } catch (e) {
    console.error('loadMessages error', e)
  } finally {
    loading.value = false
  }
}

async function sendMessage() {
  const text = inputMsg.value.trim()
  if (!text || sending.value) return
  sending.value = true
  try {
    const res = await chatAPI.sendMessage(route.params.groupId, { content: text, type: 'text' })
    if (res.data.code === 0) {
      inputMsg.value = ''
      if (inputEl.value) {
        inputEl.value.style.height = 'auto'
      }
      await loadMessages()
      scrollToBottom(true)
    }
  } catch (e) {
    console.error('sendMessage error', e)
  } finally {
    sending.value = false
  }
}

async function readMessages() {
  try { await chatAPI.readMessages(route.params.groupId) } catch (e) {}
}

onMounted(async () => {
  currentUserId.value = auth.user?.id
  await loadMessages()
  scrollToBottom()
  readMessages()
  pollTimer = setInterval(loadMessages, 5000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
/* ===== 整体布局 ===== */
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh; /* 动态视口高度，兼容移动端键盘弹出 */
  background: #EDEDED;
  overflow: hidden;
}

/* ===== 顶部导航栏 ===== */
.chat-header {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: #F7F7F7;
  border-bottom: 1px solid #E0E0E0;
  min-height: 50px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.back-btn {
  background: none;
  border: none;
  padding: 4px 8px 4px 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  color: #333;
}

.back-arrow {
  font-size: 26px;
  font-weight: 300;
  line-height: 1;
  color: #333;
}

.header-title {
  flex: 1;
  text-align: center;
  font-size: 17px;
  font-weight: 600;
  color: #191919;
}

.member-count {
  font-size: 15px;
  font-weight: 400;
  color: #888;
}

.header-right {
  width: 40px;
}

/* ===== 消息列表区 ===== */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px 10px 6px;
  -webkit-overflow-scrolling: touch;
}

.loading-wrap {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #ddd;
  border-top-color: #07C160;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ===== 时间分隔线 ===== */
.msg-time-divider {
  text-align: center;
  font-size: 12px;
  color: #999;
  background: rgba(0,0,0,0.04);
  display: inline-block;
  padding: 3px 10px;
  border-radius: 10px;
  margin: 10px auto 8px;
  display: flex;
  justify-content: center;
}

/* ===== 消息行 ===== */
.msg-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 14px;
  gap: 8px;
}

.msg-row.is-mine {
  flex-direction: row-reverse;
}

/* ===== 头像 ===== */
.msg-avatar {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
}

.avatar-img {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  object-fit: cover;
}

.avatar-placeholder {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  background: #B2C3A4;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  font-weight: 600;
  color: #fff;
  text-transform: uppercase;
}

.avatar-mine {
  background: #07C160;
}

/* ===== 消息内容 ===== */
.msg-content {
  max-width: calc(100% - 100px);
  display: flex;
  flex-direction: column;
}

.is-mine .msg-content {
  align-items: flex-end;
}

.msg-sender-name {
  font-size: 12px;
  color: #888;
  margin-bottom: 3px;
  padding-left: 2px;
}

/* ===== 气泡 ===== */
.msg-bubble-wrap {
  position: relative;
}

.msg-bubble {
  padding: 9px 12px;
  border-radius: 6px;
  font-size: 15px;
  line-height: 1.55;
  word-break: break-all;
  display: inline-block;
  max-width: 100%;
  position: relative;
}

/* 对方气泡 — 白色，左侧小三角 */
.bubble-other {
  background: #FFFFFF;
  color: #1A1A1A;
  border-top-left-radius: 0;
}

.bubble-other::before {
  content: '';
  position: absolute;
  top: 10px;
  left: -7px;
  border: 5px solid transparent;
  border-right-color: #FFFFFF;
  border-left: none;
}

/* 自己气泡 — 微信绿，右侧小三角 */
.bubble-mine {
  background: #95EC69;
  color: #1A1A1A;
  border-top-right-radius: 0;
}

.bubble-mine::after {
  content: '';
  position: absolute;
  top: 10px;
  right: -7px;
  border: 5px solid transparent;
  border-left-color: #95EC69;
  border-right: none;
}

/* ===== 空状态 ===== */
.empty-chat {
  text-align: center;
  padding: 60px 20px;
  color: #999;
  font-size: 15px;
}

/* ===== 底部输入栏 ===== */
.chat-input-bar {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 8px 12px;
  padding-bottom: max(8px, env(safe-area-inset-bottom));
  background: #F7F7F7;
  border-top: 1px solid #E0E0E0;
  flex-shrink: 0;
}

.input-wrap {
  flex: 1;
  background: #FFFFFF;
  border: 1px solid #DCDCDC;
  border-radius: 6px;
  overflow: hidden;
}

.chat-input {
  width: 100%;
  border: none;
  outline: none;
  padding: 8px 10px;
  font-size: 15px;
  font-family: inherit;
  line-height: 1.5;
  resize: none;
  background: transparent;
  color: #1A1A1A;
  min-height: 36px;
  max-height: 100px;
  display: block;
}

.chat-input::placeholder {
  color: #C0C0C0;
}

/* 发送按钮 */
.send-btn {
  flex-shrink: 0;
  padding: 8px 16px;
  background: #E8E8E8;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 500;
  color: #888;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
  align-self: flex-end;
  height: 36px;
}

.send-btn.send-btn-active {
  background: #07C160;
  color: #fff;
}

.send-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
</style>
