<template>
  <div class="wx-messages">
    <!-- 顶部导航 -->
    <div class="wx-navbar">
      <span class="wx-title">微信</span>
      <span class="wx-nav-right" @click="showAction = !showAction">＋</span>
    </div>

    <!-- 搜索栏 -->
    <div class="wx-search-bar" @click="$router.push('/search')">
      <div class="wx-search-inner">
        <span class="wx-search-icon">🔍</span>
        <span class="wx-search-placeholder">搜索</span>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="wx-msg-list">
      <div v-if="loading" class="wx-loading">加载中...</div>
      <div v-else-if="mergedList.length === 0" class="wx-empty">
        <div class="wx-empty-icon">💬</div>
        <p>暂无消息</p>
        <p class="wx-empty-hint">和好友聊聊天吧</p>
      </div>
      <div
        v-else
        v-for="item in mergedList"
        :key="item._key"
        class="wx-msg-item"
        @click="onMsgClick(item)"
      >
        <!-- 头像 -->
        <div class="wx-msg-avatar-wrap">
          <div class="wx-msg-avatar" :style="item._avatarBg">
            <img v-if="item._avatar" :src="item._avatar" />
            <span v-else>{{ item._initial }}</span>
          </div>
          <span v-if="item._unread" class="wx-msg-badge">{{ item._unread > 99 ? '99+' : item._unread }}</span>
        </div>

        <!-- 内容区 -->
        <div class="wx-msg-content">
          <div class="wx-msg-top">
            <span class="wx-msg-name">{{ item._name }}</span>
            <span class="wx-msg-time">{{ item._time }}</span>
          </div>
          <div class="wx-msg-bottom">
            <span class="wx-msg-preview">{{ item._preview }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作弹窗 -->
    <div v-if="showAction" class="wx-actionsheet-mask" @click="showAction = false">
      <div class="wx-actionsheet" @click.stop>
        <div class="wx-actionsheet-item" @click="showAction = false; $router.push('/contacts')">发起群聊</div>
        <div class="wx-actionsheet-item" @click="showAction = false; $router.push('/contacts')">添加朋友</div>
        <div class="wx-actionsheet-cancel" @click="showAction = false">取消</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { chatAPI, usersAPI } from '@/api'

const router = useRouter()
const loading = ref(true)
const groups = ref([])
const privates = ref([])
const pendingCount = ref(0)
const showAction = ref(false)
let pollTimer = null

// 合并群聊 + 私信为一个按时间排序的列表
const mergedList = computed(() => {
  const list = []
  
  // 群聊
  if (Array.isArray(groups.value)) {
    groups.value.forEach(g => {
      list.push({
        _key: 'g-' + g.group_id,
        _type: 'group',
        _name: g.name || '群聊',
        _avatar: g.avatar_url || '',
        _initial: (g.name || '群')[0],
        _avatarBg: {},
        _preview: g.last_message || '暂无消息',
        _time: formatTime(g.last_time),
        _unread: g.unread_count || 0,
        _targetId: g.group_id
      })
    })
  }
  
  // 私聊
  if (Array.isArray(privates.value)) {
    privates.value.forEach(p => {
      list.push({
        _key: 'p-' + p.user_id,
        _type: 'private',
        _name: p.nickname || '用户',
        _avatar: p.avatar_url || '',
        _initial: (p.nickname || '?')[0],
        _avatarBg: {},
        _preview: p.last_message || '暂无消息',
        _time: formatTime(p.last_time),
        _unread: p.unread_count || 0,
        _targetId: p.user_id
      })
    })
  }
  
  // 按时间倒序
  list.sort((a, b) => {
    const ta = a._time || ''
    const tb = b._time || ''
    return tb.localeCompare(ta)
  })
  
  return list
})

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) {
    return d.toTimeString().slice(0, 5)
  }
  return (d.getMonth() + 1) + '/' + d.getDate()
}

function onMsgClick(item) {
  if (item._type === 'group') {
    router.push('/chat/group/' + item._targetId)
  } else {
    router.push('/chat/private/' + item._targetId)
  }
}

async function loadData() {
  try {
    const [gr, pr] = await Promise.all([
      chatAPI.groupMessages().catch(() => ({ data: { code: -1, data: { items: [] } } })),
      chatAPI.privateMessages().catch(() => ({ data: { code: -1, data: { items: [] } } }))
    ])
    if (gr.data.code === 0) groups.value = gr.data.data.items || []
    if (pr.data.code === 0) privates.value = pr.data.data.items || []
  } catch (e) {}
  loading.value = false
}

async function loadPendingRequests() {
  try {
    const res = await usersAPI.pendingFriendRequests()
    if (res.data.code === 0) {
      pendingCount.value = (res.data.data.items || []).length
    }
  } catch (e) {}
}

onMounted(() => {
  loadData()
  loadPendingRequests()
  pollTimer = setInterval(loadData, 30000)
})

onUnmounted(() => {
  clearInterval(pollTimer)
})
</script>

<style scoped>
.wx-messages { background: #fff; min-height: 100vh; padding-bottom: 60px; }

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
  display: flex; align-items: center; justify-content: center; gap: 4px;
  background: #fff; border-radius: 8px; height: 32px; padding: 0 10px;
}
.wx-search-icon { font-size: 13px; opacity: 0.4; flex-shrink: 0; }
.wx-search-placeholder { font-size: 13px; color: #B0B0B0; }

/* === 消息列表 === */
.wx-msg-list { background: #fff; }
.wx-msg-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px; cursor: pointer; position: relative;
}
.wx-msg-item::after {
  content: ''; position: absolute; left: 68px; right: 0; bottom: 0;
  height: 0.5px; background: #E5E5E5;
}
.wx-msg-item:active { background: #F5F5F5; }

.wx-msg-avatar-wrap { position: relative; flex-shrink: 0; }
.wx-msg-avatar {
  width: 48px; height: 48px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; color: #fff; overflow: hidden;
  background: linear-gradient(135deg, #07C160, #10d56a);
}
.wx-msg-avatar img { width: 100%; height: 100%; object-fit: cover; }
.wx-msg-badge {
  position: absolute; top: -4px; right: -4px;
  background: #FA5151; color: #fff; font-size: 11px;
  min-width: 18px; height: 18px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  padding: 0 5px; font-weight: 600;
}

.wx-msg-content { flex: 1; overflow: hidden; }
.wx-msg-top { display: flex; justify-content: space-between; align-items: center; }
.wx-msg-name { font-size: 16px; color: #111; font-weight: 400; }
.wx-msg-time { font-size: 12px; color: #999; }
.wx-msg-bottom { margin-top: 4px; }
.wx-msg-preview { font-size: 14px; color: #999; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block; }

/* === 操作弹窗 === */
.wx-actionsheet-mask {
  position: fixed; inset: 0; top: 44px;
  background: rgba(0,0,0,0.3); z-index: 200;
  display: flex; justify-content: center;
}
.wx-actionsheet {
  width: 100%; max-height: 70vh; overflow-y: auto;
  background: #fff; border-radius: 0 0 12px 12px;
  padding-top: 8px;
}
.wx-actionsheet-item {
  padding: 14px 20px; font-size: 16px; color: #111;
  cursor: pointer; text-align: center;
}
.wx-actionsheet-item:active { background: #F5F5F5; }
.wx-actionsheet-cancel {
  padding: 14px 20px; font-size: 16px; color: #576B95;
  cursor: pointer; text-align: center; font-weight: 500;
  border-top: 6px solid #EDEDED;
}
.wx-actionsheet-cancel:active { background: #F5F5F5; }

/* === 空状态 === */
.wx-loading { text-align: center; padding: 40px 0; color: #999; font-size: 14px; }
.wx-empty { text-align: center; padding: 60px 0; color: #999; }
.wx-empty-icon { font-size: 48px; margin-bottom: 12px; }
.wx-empty-hint { font-size: 13px; margin-top: 4px; }
</style>
