<template>
  <div class="wx-contacts">
    <!-- 顶部导航 -->
    <div class="wx-navbar">
      <span class="wx-title">通讯录</span>
      <span class="wx-nav-right" @click="$router.push('/search?type=add')">＋</span>
    </div>

    <!-- 搜索栏 -->
    <div class="wx-search-bar">
      <div class="wx-search-inner">
        <span class="wx-search-icon">&#128269;</span>
        <input
          v-model="keyword"
          class="wx-search-input"
          placeholder="搜索"
        />
      </div>
    </div>

    <!-- 功能入口 -->
    <div class="wx-func-list">
      <div class="wx-func-item" @click="$router.push('/contacts/requests')">
        <div class="wx-func-avatar wx-func-avatar--newfriend">
          <span>&#128075;</span>
        </div>
        <div class="wx-func-info">
          <span class="wx-func-name">新的朋友</span>
        </div>
        <span v-if="pendingCount" class="wx-badge">{{ pendingCount }}</span>
      </div>
      <div class="wx-func-item" @click="$router.push('/groups')">
        <div class="wx-func-avatar wx-func-avatar--group">
          <span>&#128101;</span>
        </div>
        <div class="wx-func-info">
          <span class="wx-func-name">群聊</span>
        </div>
      </div>
      <div class="wx-func-item" @click="$router.push('/contacts/labels')">
        <div class="wx-func-avatar wx-func-avatar--label">
          <span>&#128204;</span>
        </div>
        <div class="wx-func-info">
          <span class="wx-func-name">标签</span>
        </div>
      </div>
    </div>

    <!-- 好友列表 -->
    <div class="wx-friend-list">
      <div v-if="loadingFriends" class="wx-loading">加载中...</div>
      <div v-else-if="friends.length === 0 && !keyword.trim()" class="wx-empty">
        <p>还没有好友，去搜索添加吧</p>
      </div>
      <div v-else>
        <div
          v-for="(group, idx) in groupedFriends"
          :key="group.letter"
        >
          <div class="wx-letter-header">{{ group.letter }}</div>
          <div
            v-for="f in group.members"
            :key="f.user_id"
            class="wx-friend-item"
            @click="$router.push('/profile/' + f.user_id)"
          >
            <div class="wx-friend-avatar">
              <img v-if="f.avatar_url" :src="f.avatar_url" />
              <span v-else>{{ (f.nickname || '?')[0] }}</span>
            </div>
            <div class="wx-friend-name">{{ f.nickname }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 字母索引条 -->
    <div class="wx-index-bar" v-if="groupedFriends.length > 0">
      <span
        v-for="group in groupedFriends"
        :key="group.letter"
        class="wx-index-letter"
        @click="scrollToLetter(group.letter)"
      >{{ group.letter }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usersAPI } from '@/api'

const keyword = ref('')
const friends = ref([])
const pendingRequests = ref([])
const pendingCount = ref(0)
const loadingFriends = ref(false)

const myId = computed(() => {
  const token = localStorage.getItem('token')
  try { return JSON.parse(atob(token.split('.')[1])).user_id } catch(e) { return null }
})

const groupedFriends = computed(() => {
  const list = keyword.value.trim() ? filteredFriends.value : friends.value
  const groups = {}
  list.forEach(f => {
    const letter = (f.nickname || '?')[0].toUpperCase()
    const key = /[A-Z]/.test(letter) ? letter : '#'
    if (!groups[key]) groups[key] = []
    groups[key].push(f)
  })
  return Object.keys(groups).sort().map(letter => ({
    letter,
    members: groups[letter]
  }))
})

const filteredFriends = computed(() => {
  if (!keyword.value.trim()) return friends.value
  const kw = keyword.value.trim().toLowerCase()
  return friends.value.filter(f =>
    (f.nickname || '').toLowerCase().includes(kw)
  )
})

function scrollToLetter(letter) {
  const headers = document.querySelectorAll('.wx-letter-header')
  for (let h of headers) {
    if (h.textContent.trim() === letter) {
      h.scrollIntoView({ behavior: 'smooth', block: 'start' })
      break
    }
  }
}

async function loadFriends() {
  loadingFriends.value = true
  try {
    const res = await usersAPI.friends()
    if (res.data.code === 0) {
      friends.value = res.data.data.items || []
    }
  } catch (e) {
    console.error('获取好友列表失败', e)
  } finally {
    loadingFriends.value = false
  }
}

async function loadPendingRequests() {
  try {
    const res = await usersAPI.pendingFriendRequests()
    if (res.data.code === 0) {
      pendingRequests.value = res.data.data.items || []
      pendingCount.value = pendingRequests.value.length
    }
  } catch (e) {
    console.error('获取好友请求失败', e)
  }
}

onMounted(() => {
  loadFriends()
  loadPendingRequests()
})
</script>

<style scoped>
.wx-contacts { background: #EDEDED; min-height: 100vh; padding-bottom: 60px; }

/* === 顶部导航 === */
.wx-navbar {
  position: sticky; top: 0; z-index: 100;
  display: flex; align-items: center; justify-content: center;
  height: 44px; background: #EDEDED;
  border-bottom: 0.5px solid #D9D9D9;
}
.wx-title { font-size: 17px; font-weight: 600; color: #111; }
.wx-nav-right {
  position: absolute; right: 16px; font-size: 22px; color: #07C160;
  cursor: pointer; font-weight: 300;
}

/* === 搜索栏 === */
.wx-search-bar { padding: 6px 12px 6px; background: #EDEDED; }
.wx-search-inner {
  display: flex; align-items: center; gap: 4px;
  background: #fff; border-radius: 8px; height: 32px; padding: 0 10px;
}
.wx-search-icon { font-size: 13px; opacity: 0.4; flex-shrink: 0; }
.wx-search-input {
  flex: 1; border: none; outline: none; background: transparent;
  font-size: 13px; color: #111;
}
.wx-search-input::placeholder { color: #B0B0B0; }

/* === 功能入口 === */
.wx-func-list { background: #fff; margin-top: 8px; }
.wx-func-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px; cursor: pointer; position: relative;
}
.wx-func-item::after {
  content: ''; position: absolute; left: 60px; right: 0; bottom: 0;
  height: 0.5px; background: #E5E5E5;
}
.wx-func-avatar {
  width: 40px; height: 40px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; color: #fff; flex-shrink: 0;
}
.wx-func-avatar--newfriend { background: #FA5151; }
.wx-func-avatar--group { background: #07C160; }
.wx-func-avatar--label { background: #FFC300; }
.wx-func-info { flex: 1; }
.wx-func-name { font-size: 15px; color: #111; }
.wx-badge {
  background: #FA5151; color: #fff; font-size: 11px;
  min-width: 18px; height: 18px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  padding: 0 5px; font-weight: 600;
}

/* === 好友列表 === */
.wx-friend-list { background: #fff; margin-top: 8px; position: relative; padding-right: 20px; }
.wx-letter-header {
  padding: 2px 16px; font-size: 12px; color: #999;
  background: #F5F5F5; position: sticky; top: 44px; z-index: 10;
  border-bottom: 0.5px solid #E5E5E5;
}
.wx-friend-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px; cursor: pointer; position: relative;
}
.wx-friend-item::after {
  content: ''; position: absolute; left: 60px; right: 0; bottom: 0;
  height: 0.5px; background: #E5E5E5;
}
.wx-friend-item:active { background: #F5F5F5; }
.wx-friend-avatar {
  width: 40px; height: 40px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; color: #fff; overflow: hidden; flex-shrink: 0;
  background: linear-gradient(135deg, #FF6B35, #FF8C5A);
}
.wx-friend-avatar img { width: 100%; height: 100%; object-fit: cover; }
.wx-friend-name { flex: 1; font-size: 15px; color: #111; }

/* === 字母索引条（微信风格） === */
.wx-index-bar {
  position: fixed; right: 2px; top: 90px; bottom: 120px;
  display: flex; flex-direction: column;
  align-items: center; justify-content: space-around;
  z-index: 1000; padding: 8px 3px;
}
.wx-index-letter {
  font-size: 12px; line-height: 1.3; color: #07C160;
  padding: 2px 3px; text-align: center;
  cursor: pointer; user-select: none;
  font-weight: 500; min-width: 14px;
}
.wx-index-letter:active {
  color: #fff; background: #07C160; border-radius: 6px;
}

/* === 空状态 / 加载中 === */
.wx-loading { text-align: center; padding: 40px 0; color: #999; font-size: 14px; }
.wx-empty { text-align: center; padding: 60px 0; color: #999; font-size: 15px; }
</style>
