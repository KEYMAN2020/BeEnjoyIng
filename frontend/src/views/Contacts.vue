<template>
  <div class="contacts-page">
    <!-- ═══ Teal Header ═══ -->
    <div class="c-header">
      <div class="c-header-row">
        <span class="c-back" @click="$router.back()">←</span>
        <span class="c-title">通讯录</span>
        <span class="c-add" @click="$router.push('/search?type=add')">＋</span>
      </div>
    </div>

    <!-- ═══ Search Bar ═══ -->
    <div class="c-search">
      <div class="c-search-inner">
        <span class="c-search-icon">🔍</span>
        <input v-model="keyword" class="c-search-input" placeholder="搜索" />
      </div>
    </div>

    <!-- ═══ Function Entries (white card) ═══ -->
    <div class="c-card">
      <div class="c-item" @click="$router.push('/contacts/requests')">
        <div class="c-avatar c-avatar--red"><span>👋</span></div>
        <span class="c-name">新的朋友</span>
        <span v-if="pendingCount" class="c-badge">{{ pendingCount }}</span>
        <span class="c-arrow">›</span>
      </div>
      <div class="c-item" @click="$router.push('/groups')">
        <div class="c-avatar c-avatar--green"><span>👥</span></div>
        <span class="c-name">群聊</span>
        <span class="c-arrow">›</span>
      </div>
      <div class="c-item" @click="$router.push('/contacts/labels')">
        <div class="c-avatar c-avatar--gold"><span>📌</span></div>
        <span class="c-name">标签</span>
        <span class="c-arrow">›</span>
      </div>
    </div>

    <!-- ═══ Friend List (white card) ═══ -->
    <div class="c-card c-card-friends">
      <div v-if="loadingFriends" class="c-empty">加载中...</div>
      <div v-else-if="friends.length === 0 && !keyword.trim()" class="c-empty">还没有好友，去搜索添加吧</div>
      <div v-else>
        <div v-for="(group, idx) in groupedFriends" :key="group.letter">
          <div class="c-letter">{{ group.letter }}</div>
          <div v-for="f in group.members" :key="f.user_id" class="c-item" @click="$router.push('/profile/' + f.user_id)">
            <div class="c-friend-avatar">
              <img v-if="f.avatar_url" :src="f.avatar_url" />
              <span v-else>{{ (f.nickname || '?')[0] }}</span>
            </div>
            <span class="c-name">{{ f.nickname }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ Alphabet Index ═══ -->
    <div class="c-index" v-if="groupedFriends.length > 0">
      <span v-for="g in groupedFriends" :key="g.letter" class="c-index-letter" @click="scrollToLetter(g.letter)">{{ g.letter }}</span>
    </div>

    <div style="height:70px"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usersAPI } from '@/api'
import { pinyin } from 'pinyin-pro'

const keyword = ref('')
const friends = ref([])
const pendingCount = ref(0)
const loadingFriends = ref(false)

function getInitial(nickname) {
  if (!nickname) return '#'
  const first = nickname[0]
  // Latin letter → use directly
  if (/[a-zA-Z]/.test(first)) return first.toUpperCase()
  // Chinese character → get pinyin initial
  try {
    const py = pinyin(first, { pattern: 'first', toneType: 'none' })
    if (py && /[a-zA-Z]/.test(py)) return py.toUpperCase()
  } catch(e) {}
  return '#'
}

const groupedFriends = computed(() => {
  const list = keyword.value.trim() ? filteredFriends.value : friends.value
  const groups = {}
  list.forEach(f => {
    const key = getInitial(f.nickname)
    if (!groups[key]) groups[key] = []
    groups[key].push(f)
  })
  return Object.keys(groups).sort().map(letter => ({ letter, members: groups[letter] }))
})

const filteredFriends = computed(() => {
  if (!keyword.value.trim()) return friends.value
  const kw = keyword.value.trim().toLowerCase()
  return friends.value.filter(f => (f.nickname || '').toLowerCase().includes(kw))
})

function scrollToLetter(letter) {
  const headers = document.querySelectorAll('.c-letter')
  for (let h of headers) { if (h.textContent.trim() === letter) { h.scrollIntoView({ behavior: 'smooth', block: 'start' }); break } }
}

async function loadFriends() {
  loadingFriends.value = true
  try {
    const res = await usersAPI.friends()
    if (res.data.code === 0) friends.value = res.data.data.items || []
  } catch (e) {}
  loadingFriends.value = false
}

async function loadPending() {
  try {
    const res = await usersAPI.pendingFriendRequests()
    if (res.data.code === 0) pendingCount.value = (res.data.data.items || []).length
  } catch (e) {}
}

onMounted(() => { loadFriends(); loadPending() })
</script>

<style scoped>
.contacts-page { background: #F2F4F5; min-height: 100vh; font-family: 'PingFang SC', sans-serif }

/* ═══ Header ═══ */
.c-header { background: linear-gradient(180deg, #06D6A0 0%, #0096C7 100%); padding: 12px 0 14px }
.c-header-row { display: flex; align-items: center; padding: 0 16px }
.c-back { color: #fff; font-size: 18px; cursor: pointer; width: 36px }
.c-title { flex: 1; text-align: center; color: #fff; font-size: 17px; font-weight: 600 }
.c-add { color: #fff; font-size: 22px; cursor: pointer; width: 36px; text-align: right; font-weight: 300 }

/* ═══ Search ═══ */
.c-search { padding: 8px 16px }
.c-search-inner { display: flex; align-items: center; gap: 6px; background: #fff; border-radius: 8px; height: 36px; padding: 0 12px; box-shadow: 0 1px 3px rgba(0,0,0,.04) }
.c-search-icon { font-size: 14px; opacity: .4 }
.c-search-input { flex: 1; border: none; outline: none; font-size: 14px; color: #333; background: transparent }
.c-search-input::placeholder { color: #B0B0B0 }

/* ═══ Cards ═══ */
.c-card { background: #fff; border-radius: 12px; margin: 0 16px 10px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.04) }
.c-card-friends { padding-bottom: 0 }

/* ═══ Items ═══ */
.c-item { display: flex; align-items: center; padding: 12px 16px; cursor: pointer; border-bottom: 1px solid #f5f5f5; position: relative }
.c-item:last-child { border-bottom: none }
.c-item:active { background: #f9f9f9 }

/* Function avatars */
.c-avatar { width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; color: #fff; flex-shrink: 0; margin-right: 12px }
.c-avatar--red { background: #FF6B6B }
.c-avatar--green { background: #06D6A0 }
.c-avatar--gold { background: #FFB800 }
.c-name { flex: 1; font-size: 15px; color: #333 }
.c-arrow { color: #ccc; font-size: 16px }
.c-badge { background: #FF6B6B; color: #fff; font-size: 11px; min-width: 18px; height: 18px; border-radius: 9px; display: flex; align-items: center; justify-content: center; padding: 0 5px; margin-right: 8px; font-weight: 600 }

/* Friend avatars */
.c-friend-avatar { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; color: #fff; overflow: hidden; flex-shrink: 0; margin-right: 12px; background: linear-gradient(135deg, #06D6A0, #0096C7) }
.c-friend-avatar img { width: 100%; height: 100%; object-fit: cover }

/* Letter headers */
.c-letter { padding: 4px 16px; font-size: 12px; color: #999; background: #F5F7F8; border-bottom: 1px solid #f0f0f0; position: sticky; top: 0; z-index: 2 }

/* ═══ Index ═══ */
.c-index { position: fixed; right: 3px; top: 130px; bottom: 100px; display: flex; flex-direction: column; align-items: center; justify-content: space-around; z-index: 100; padding: 4px 2px }
.c-index-letter { font-size: 11px; color: #0096C7; padding: 2px 4px; cursor: pointer; user-select: none; min-width: 14px; text-align: center; font-weight: 500 }
.c-index-letter:active { color: #fff; background: #0096C7; border-radius: 6px }

/* ═══ Empty/Loading ═══ */
.c-empty { text-align: center; padding: 50px 0; color: #999; font-size: 14px }
</style>
