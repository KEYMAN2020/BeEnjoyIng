<template>
  <div class="pvtc-chat-page">
    <!-- Header -->
    <div class="pvtc-header">
      <button class="pvtc-back" @click="$router.back()">‹</button>
      <div class="pvtc-title">{{ otherUser?.nickname || '私聊' }}</div>
      <div class="pvtc-header-right">
        <span class="pvtc-info-btn" @click="$router.push('/profile/' + otherId)">···</span>
      </div>
    </div>

    <!-- Messages -->
    <div class="pvtc-body" ref="msgArea">
      <div v-if="loading" class="pvtc-loading">加载中...</div>
      <div v-else-if="messages.length === 0" class="pvtc-empty">
        暂无消息记录<br>发送第一条消息吧
      </div>
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="pvtc-msg-row"
        :class="{ 'is-me': msg.sender_id === myId }"
      >
        <div
          class="pvtc-bubble"
          :class="msg.sender_id === myId ? 'bubble-me' : 'bubble-other'"
        >
          {{ msg.content }}
        </div>
        <div class="pvtc-time">{{ formatTime(msg.created_at) }}</div>
      </div>
    </div>

    <!-- Input -->
    <div class="pvtc-input-bar">
      <input
        v-model="inputText"
        @keydown.enter="sendMsg"
        placeholder="输入消息..."
        class="pvtc-input"
        ref="inputEl"
      />
      <button
        class="pvtc-send-btn"
        @click="sendMsg"
        :disabled="!inputText.trim()"
      >发送</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usersAPI } from '@/api'

const route = useRoute()
const router = useRouter()
const otherId = route.params.id
const messages = ref([])
const otherUser = ref(null)
const inputText = ref('')
const loading = ref(true)
const myId = ref(null)
const msgArea = ref(null)
const inputEl = ref(null)

function formatTime(d) {
  if (!d) return ''
  return d.slice(5, 16) || d
}

async function loadMessages() {
  loading.value = true
  try {
    const res = await usersAPI.messagesWith(otherId)
    if (res.data.code === 0) {
      messages.value = res.data.data.messages || []
      otherUser.value = res.data.data.other_user || null
      await nextTick()
      scrollBottom()
    }
  } catch (e) {}
  loading.value = false
}

function scrollBottom() {
  if (msgArea.value) msgArea.value.scrollTop = msgArea.value.scrollHeight
}

async function sendMsg() {
  const txt = inputText.value.trim()
  if (!txt) return
  inputText.value = ''
  try {
    const res = await usersAPI.sendMessage({ receiver_id: parseInt(otherId), content: txt })
    if (res.data.code === 0) {
      loadMessages()
    } else {
      alert(res.data.message || '发送失败')
    }
  } catch (e) { alert('网络错误') }
}

onMounted(() => {
  const token = localStorage.getItem('token')
  if (token) {
    try { myId.value = JSON.parse(atob(token.split('.')[1])).user_id } catch (e) {}
  }
  loadMessages()
  setTimeout(() => { if (inputEl.value) inputEl.value.focus() }, 300)
})
</script>

<style scoped>
.pvtc-chat-page { display: flex; flex-direction: column; height: 100vh; background: #EDEDED; }

.pvtc-header {
  display: flex; align-items: center; padding: 0 12px; height: 44px;
  background: #F7F7F7; border-bottom: 1px solid #E0E0E0;
  position: sticky; top: 0; z-index: 10; flex-shrink: 0;
}
.pvtc-back {
  background: none; border: none; font-size: 28px; color: #333;
  cursor: pointer; padding: 0 8px 0 0; line-height: 1; font-weight: 300;
}
.pvtc-title { flex: 1; text-align: center; font-size: 17px; font-weight: 600; color: #191919; }
.pvtc-header-right { width: 60px; display: flex; justify-content: flex-end; }
.pvtc-info-btn {
  font-size: 20px; color: #333; cursor: pointer; padding: 4px 8px;
  font-weight: 600; letter-spacing: 1px;
}

.pvtc-body { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; }
.pvtc-msg-row { margin-bottom: 16px; display: flex; flex-direction: column; align-items: flex-start; }
.pvtc-msg-row.is-me { align-items: flex-end; }

.pvtc-bubble { max-width: 72%; padding: 10px 14px; border-radius: 16px; font-size: 15px; line-height: 1.5; word-break: break-word; }
.bubble-other { background: #fff; color: #333; border-radius: 4px 16px 16px 16px; box-shadow: 0 1px 2px rgba(0,0,0,.05); }
.bubble-me { background: #95EC69; color: #2D2D2D; border-radius: 16px 4px 16px 16px; }

.pvtc-time { font-size: 10px; color: #999; margin: 3px 4px 0; }

.pvtc-input-bar {
  display: flex; align-items: center; padding: 8px 12px;
  padding-bottom: max(8px, env(safe-area-inset-bottom));
  background: #F7F7F7; border-top: 1px solid #E0E0E0; flex-shrink: 0;
}
.pvtc-input {
  flex: 1; padding: 10px 14px; border: 1px solid #ddd; border-radius: 20px;
  font-size: 15px; outline: none; margin-right: 8px; background: #fff;
}
.pvtc-send-btn {
  background: #07C160; color: #fff; border: none; padding: 10px 20px;
  border-radius: 20px; font-size: 14px; font-weight: 600; cursor: pointer;
}
.pvtc-send-btn:disabled { background: #ccc; cursor: not-allowed; }

.pvtc-loading, .pvtc-empty { text-align: center; color: #999; padding: 60px 20px; font-size: 15px; }
</style>
