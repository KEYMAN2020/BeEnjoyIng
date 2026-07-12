<template>
  <div class="msg-page">
    <!-- ═══ Teal Header ═══ -->
    <div class="msg-header">
      <div class="msg-header-row">
        <span class="msg-title">消息</span>
        <span class="msg-plus" @click="showAction = !showAction">＋</span>
      </div>
    </div>

    <!-- ═══ Search Bar ═══ -->
    <div class="msg-search" @click="$router.push('/search')">
      <div class="msg-search-inner">
        <span class="msg-search-icon">🔍</span>
        <span class="msg-search-text">搜索</span>
      </div>
    </div>

    <!-- ═══ Message List ═══ -->
    <div class="msg-list">
      <div v-if="loading" class="msg-empty">加载中...</div>
      <div v-else-if="mergedList.length === 0" class="msg-empty">
        <div class="msg-empty-icon">💬</div>
        <p>暂无消息</p>
        <p class="msg-empty-hint">和好友聊聊天吧</p>
      </div>
      <div v-else v-for="item in mergedList" :key="item._key" class="msg-item" @click="onMsgClick(item)">
        <div class="msg-avatar-wrap">
          <!-- 群聊：九宫格头像 -->
          <div v-if="item._type === 'group' && item._members && item._members.length > 0" class="group-grid" :class="gridClass(item._members.length, item._memberCount)">
            <div v-for="(m, mi) in gridCells(item)" :key="mi" class="grid-cell">
              <img v-if="m.avatar_url && !failedImgs.has(m.avatar_url)" :src="m.avatar_url" class="grid-img" @error="onImgError(m.avatar_url)" loading="lazy" />
              <span v-else class="grid-text">{{ (m.nickname || '?')[0] }}</span>
              <!-- 第9个位置：超过9人时显示剩余人数 -->
              <span v-if="mi === 8 && item._memberCount > 9" class="grid-more">+{{ item._memberCount - 8 }}</span>
            </div>
          </div>
          <!-- 群聊：无成员时退化单头像 -->
          <div v-else-if="item._type === 'group'" class="msg-avatar">
            <img v-if="item._avatar && !failedImgs.has(item._avatar)" :src="item._avatar" @error="onImgError(item._avatar)" loading="lazy" />
            <span v-else>{{ item._initial }}</span>
          </div>
          <!-- 私聊：单头像 -->
          <div v-else class="msg-avatar">
            <img v-if="item._avatar && !failedImgs.has(item._avatar)" :src="item._avatar" @error="onImgError(item._avatar)" loading="lazy" />
            <span v-else>{{ item._initial }}</span>
          </div>
          <span v-if="item._unread" class="msg-badge">{{ item._unread > 99 ? '99+' : item._unread }}</span>
        </div>
        <div class="msg-content">
          <div class="msg-row">
            <span class="msg-name">{{ item._name }}</span>
            <span class="msg-time">{{ item._time }}</span>
          </div>
          <div class="msg-preview">{{ item._preview }}</div>
        </div>
      </div>
    </div>

    <!-- ═══ ActionSheet ═══ -->
    <div v-if="showAction" class="msg-sheet-mask" @click="showAction = false">
      <div class="msg-sheet" @click.stop>
        <div class="msg-sheet-item" @click="showAction = false; $router.push('/contacts')">发起群聊</div>
        <div class="msg-sheet-item" @click="showAction = false; $router.push('/contacts')">添加朋友</div>
        <div class="msg-sheet-cancel" @click="showAction = false">取消</div>
      </div>
    </div>

    <div style="height:70px"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { chatAPI, usersAPI } from '@/api'
import { socketService } from '@/socket'

const router = useRouter()
const loading = ref(true)
const groups = ref([])
const privates = ref([])
const pendingCount = ref(0)
const showAction = ref(false)

// 图片加载失败追踪（避免无限重试）
const failedImgs = ref(new Set())

function onImgError(url) {
  if (url) failedImgs.value = new Set([...failedImgs.value, url])
}

// 九宫格单元格（最多9格）
function gridCells(item) {
  const members = item._members || []
  if (members.length <= 9) return members.slice(0, 9)
  // >9人：显示前8人 + 第9格占位（由模板渲染数字）
  return members.slice(0, 9)
}

// 九宫格 CSS class
function gridClass(len, total) {
  if (total > 9 || len >= 9) return 'grid-9'
  if (len === 1) return 'grid-1'
  if (len <= 4) return 'grid-4'
  return 'grid-9'
}

// 独立未读计数器（使用 ref 确保深度响应）
const unreadCounts = ref({})
let myUserId = null
let pollTimer = null

const mergedList = computed(() => {
  const list = []
  if (Array.isArray(groups.value)) {
    groups.value.forEach(g => {
      const key = 'g-' + g.id
      const unread = unreadCounts.value[key] !== undefined ? unreadCounts.value[key] : (g.unread_count || 0)
      list.push({
        _key: key, _type: 'group', _name: g.name || '群聊',
        _avatar: g.avatar || '', _initial: (g.name || '群')[0],
        _preview: g.last_message || '暂无消息',
        _time: formatTime(g.last_message_at), _sortTime: g.last_message_at ? new Date(g.last_message_at).getTime() : 0,
        _unread: unread, _targetId: g.id,
        _members: g.members || [], _memberCount: g.member_count || 0
      })
    })
  }
  if (Array.isArray(privates.value)) {
    privates.value.forEach(p => {
      const other = p.other_user || {}
      const key = 'p-' + (other.user_id || p.message_id)
      const base = other.user_id && !p.is_read ? 1 : 0
      const unread = unreadCounts.value[key] !== undefined ? unreadCounts.value[key] : base
      list.push({
        _key: key, _type: 'private',
        _name: other.nickname || '用户', _avatar: other.avatar_url || '',
        _initial: (other.nickname || '?')[0], _avatarBg: {},
        _preview: p.content || '暂无消息',
        _time: formatTime(p.created_at), _sortTime: p.created_at ? new Date(p.created_at).getTime() : 0,
        _unread: unread, _targetId: other.user_id
      })
    })
  }
  sortByTime(list)
  return list
})

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ''  // 无效日期保护
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const msgDay = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const diffDays = Math.floor((today - msgDay) / 86400000)

  if (diffDays === 0) return d.toTimeString().slice(0, 5)  // 今天 10:25
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) {
    const days = ['周日','周一','周二','周三','周四','周五','周六']
    return days[d.getDay()]
  }
  if (d.getFullYear() === now.getFullYear()) return (d.getMonth() + 1) + '月' + d.getDate() + '日'
  return d.getFullYear() + '年' + (d.getMonth() + 1) + '月' + d.getDate() + '日'
}

function sortByTime(list) {
  list.sort((a, b) => (b._sortTime || 0) - (a._sortTime || 0))
  return list
}

function onMsgClick(item) {
  // 进入聊天时清零该会话未读
  if (unreadCounts.value[item._key]) {
    unreadCounts.value = { ...unreadCounts.value, [item._key]: 0 }
  }
  if (item._type === 'group') router.push('/messages/' + item._targetId)
  else router.push('/chat/private/' + item._targetId)
}

/** 收到新的私信 */
function onPrivateMsg(msg) {
  if (!msg || !msg.sender_id || !msg.receiver_id) return
  const otherId = msg.sender_id === myUserId ? msg.receiver_id : msg.sender_id
  const key = 'p-' + otherId

  // 更新未读计数（只有收到的消息才+1，整个对象替换确保响应式）
  if (msg.sender_id !== myUserId) {
    unreadCounts.value = { ...unreadCounts.value, [key]: (unreadCounts.value[key] || 0) + 1 }
  }

  // 更新会话数据
  let found = false
  for (let i = 0; i < privates.value.length; i++) {
    const p = privates.value[i]
    const ou = p.other_user || {}
    if (ou.user_id === otherId || p.message_id === otherId) {
      privates.value[i] = { ...p, content: msg.content, created_at: msg.created_at, is_read: msg.sender_id === myUserId }
      found = true
      break
    }
  }
  if (!found) {
    privates.value.push({
      message_id: msg.id,
      other_user: { user_id: otherId, nickname: '', avatar_url: '' },
      msg_type: 'text',
      content: msg.content,
      is_read: msg.sender_id === myUserId,
      created_at: msg.created_at,
    })
  }
  // 触发响应式更新
  privates.value = [...privates.value]
}

/** 收到新的群消息 */
function onGroupMsg(msg) {
  if (!msg || !msg.group_id) return
  const key = 'g-' + msg.group_id
  // 只有别人发的消息才增加未读
  if (msg.sender_id !== myUserId) {
    unreadCounts.value = { ...unreadCounts.value, [key]: (unreadCounts.value[key] || 0) + 1 }
  }

  let found = false
  for (let i = 0; i < groups.value.length; i++) {
    if (groups.value[i].id === msg.group_id) {
      groups.value[i] = {
        ...groups.value[i],
        last_message: msg.content,
        last_message_at: msg.created_at,
      }
      found = true
      break
    }
  }
  if (!found) {
    groups.value.push({
      id: msg.group_id,
      name: '群聊',
      avatar: '',
      last_message: msg.content,
      last_message_at: msg.created_at,
      unread_count: 1,
      members: [],
    })
  }
  groups.value = [...groups.value]
}

async function loadData() {
  try {
    const [gr, pr] = await Promise.all([
      chatAPI.groups().catch(() => ({ data: { code: -1, data: { groups: [] } } })),
      usersAPI.messages().catch(() => ({ data: { code: -1, data: { items: [] } } }))
    ])
    if (gr.data.code === 0) {
      // 群聊合并：保留 socket 更新的 last_message
      const freshGroups = gr.data.data.groups || []
      const existingMap = new Map(groups.value.map(g => [g.id, g]))
      groups.value = freshGroups.map(g => {
        const exist = existingMap.get(g.id)
        return exist && exist.last_message_at && (!g.last_message_at || new Date(exist.last_message_at) > new Date(g.last_message_at))
          ? { ...g, last_message: exist.last_message, last_message_at: exist.last_message_at }
          : g
      })
    }
    if (pr.data.code === 0) {
      // 私信合并：保留 socket 更新的最新消息
      const freshItems = pr.data.data.items || []
      const existingPm = new Map(privates.value.map(p => {
        const ou = p.other_user || {}
        return [ou.user_id || p.message_id, p]
      }))
      privates.value = freshItems.map(p => {
        const ou = p.other_user || {}
        const oid = ou.user_id || p.message_id
        const exist = existingPm.get(oid)
        if (exist && exist.created_at && new Date(exist.created_at) > new Date(p.created_at || '1970')) {
          return { ...p, content: exist.content, created_at: exist.created_at, is_read: exist.is_read }
        }
        // 用 REST unread_count 初始 unreadCounts（仅在 key 不存在时设置）
         const key = 'p-' + oid
         if (unreadCounts.value[key] === undefined) {
           unreadCounts.value = { ...unreadCounts.value, [key]: p.unread_count || 0 }
         }
        return p
      })
    }
  } catch (e) {}
  loading.value = false
}

onMounted(() => {
  // 解析当前用户 ID
  const token = localStorage.getItem('token')
  if (token) {
    try { myUserId = JSON.parse(atob(token.split('.')[1])).user_id } catch (e) {}
  }

  loadData()
  pollTimer = setInterval(loadData, 30000)

  // Socket 实时更新
  socketService.onPrivateMessage(onPrivateMsg)
  socketService.onGroupMessage(onGroupMsg)
})

onUnmounted(() => {
  clearInterval(pollTimer)
  socketService.offPrivateMessage(onPrivateMsg)
  socketService.offGroupMessage(onGroupMsg)
})
</script>

<style scoped>
.msg-page { background: #F2F4F5; min-height: 100vh; font-family: 'PingFang SC', sans-serif }

/* Header */
.msg-header { background: linear-gradient(180deg, #06D6A0 0%, #0096C7 100%); padding: 12px 0 14px }
.msg-header-row { display: flex; align-items: center; justify-content: center; padding: 0 16px; position: relative }
.msg-title { color: #fff; font-size: 17px; font-weight: 600 }
.msg-plus { position: absolute; right: 16px; color: #fff; font-size: 22px; cursor: pointer; font-weight: 300 }

/* Search */
.msg-search { padding: 8px 16px }
.msg-search-inner { display: flex; align-items: center; justify-content: center; gap: 4px; background: #fff; border-radius: 8px; height: 36px; padding: 0 10px; box-shadow: 0 1px 3px rgba(0,0,0,.04); cursor: pointer }
.msg-search-icon { font-size: 14px; opacity: .4 }
.msg-search-text { font-size: 14px; color: #B0B0B0 }

/* List */
.msg-list { background: #fff; margin: 0 16px; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.04) }
.msg-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; cursor: pointer; border-bottom: 1px solid #f5f5f5 }
.msg-item:last-child { border-bottom: none }
.msg-item:active { background: #f9f9f9 }
.msg-avatar-wrap { position: relative; flex-shrink: 0 }
.msg-avatar { width: 48px; height: 48px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: #fff; overflow: hidden; background: linear-gradient(135deg, #06D6A0, #0096C7) }
.msg-avatar img { width: 100%; height: 100%; object-fit: cover }
.msg-badge { position: absolute; top: -4px; right: -4px; background: #FF6B6B; color: #fff; font-size: 11px; min-width: 18px; height: 18px; border-radius: 9px; display: flex; align-items: center; justify-content: center; padding: 0 5px; font-weight: 600 }

/* 九宫格群聊头像 */
.group-grid {
  width: 48px; height: 48px;
  display: grid;
  gap: 1.5px;
  border-radius: 8px;
  overflow: hidden;
  background: linear-gradient(135deg, #06D6A0, #0096C7);
  flex-shrink: 0;
}
.group-grid.grid-1 { grid-template-columns: 1fr; grid-template-rows: 1fr; }
.group-grid.grid-4 { grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; }
.group-grid.grid-9 { grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(3, 1fr); }

.grid-cell {
  position: relative;
  background: rgba(255,255,255,0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.grid-cell:only-child { border-radius: 8px; }

.grid-img {
  width: 100%; height: 100%;
  object-fit: cover;
  transition: opacity 0.3s ease;
}
.grid-img:hover { opacity: 0.85; }

.grid-text {
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  line-height: 1;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.grid-more {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.35);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  backdrop-filter: blur(2px);
}
.msg-content { flex: 1; overflow: hidden }
.msg-row { display: flex; justify-content: space-between; align-items: center }
.msg-name { font-size: 16px; color: #333; font-weight: 400 }
.msg-time { font-size: 12px; color: #999 }
.msg-preview { margin-top: 4px; font-size: 14px; color: #999; overflow: hidden; text-overflow: ellipsis; white-space: nowrap }

/* ActionSheet */
.msg-sheet-mask { position: fixed; inset: 0; background: rgba(0,0,0,.3); z-index: 200; display: flex; justify-content: center; padding-top: 56px }
.msg-sheet { width: 100%; max-height: 70vh; overflow-y: auto; background: #fff; border-radius: 0 0 12px 12px; padding-top: 8px }
.msg-sheet-item { padding: 14px 20px; font-size: 16px; color: #333; cursor: pointer; text-align: center }
.msg-sheet-item:active { background: #f5f5f5 }
.msg-sheet-cancel { padding: 14px 20px; font-size: 16px; color: #0096C7; cursor: pointer; text-align: center; font-weight: 500; border-top: 6px solid #F2F4F5 }
.msg-sheet-cancel:active { background: #f5f5f5 }

/* Empty */
.msg-empty { text-align: center; padding: 60px 0; color: #999; font-size: 14px }
.msg-empty-icon { font-size: 48px; margin-bottom: 12px }
.msg-empty-hint { font-size: 13px; margin-top: 4px }
</style>
