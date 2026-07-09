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
              <span v-else>{{ (m.nickname || '?')[0] }}</span>
              <span v-if="mi === 8 && item._memberCount > 9" class="grid-more">+{{ item._memberCount - 8 }}</span>
            </div>
          </div>
          <!-- 单头像：群聊无成员 或 私聊 -->
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

const router = useRouter()
const loading = ref(true)
const groups = ref([])
const privates = ref([])
const pendingCount = ref(0)
const showAction = ref(false)
let pollTimer = null

// 图片加载失败追踪
const failedImgs = ref(new Set())
function onImgError(url) { if (url) failedImgs.value = new Set([...failedImgs.value, url]) }

// 独立未读计数器
const unreadCounts = ref({})

// 九宫格单元格
function gridCells(item) {
  const members = item._members || []
  if (members.length <= 9) return members.slice(0, 9)
  return members.slice(0, 9)
}
function gridClass(len, total) {
  if (total > 9 || len >= 9) return 'grid-9'
  if (len === 1) return 'grid-1'
  if (len <= 4) return 'grid-4'
  return 'grid-9'
}

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
      const base = (other.user_id && !p.is_read) ? 1 : 0
      const unread = unreadCounts.value[key] !== undefined ? unreadCounts.value[key] : base
      list.push({
        _key: key, _type: 'private',
        _name: other.nickname || '用户', _avatar: other.avatar_url || '',
        _initial: (other.nickname || '?')[0],
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
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const msgDay = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const diffDays = Math.floor((today - msgDay) / 86400000)
  if (diffDays === 0) return d.toTimeString().slice(0, 5)
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) { const days = ['周日','周一','周二','周三','周四','周五','周六']; return days[d.getDay()] }
  if (d.getFullYear() === now.getFullYear()) return (d.getMonth()+1)+'月'+d.getDate()+'日'
  return d.getFullYear()+'年'+(d.getMonth()+1)+'月'+d.getDate()+'日'
}

function sortByTime(list) {
  list.sort((a, b) => (b._sortTime || 0) - (a._sortTime || 0))
  return list
}

function onMsgClick(item) {
  // 进入聊天清零未读
  if (unreadCounts.value[item._key]) {
    unreadCounts.value = { ...unreadCounts.value, [item._key]: 0 }
  }
  if (item._type === 'group') router.push('/messages/' + item._targetId)
  else router.push('/chat/private/' + item._targetId)
}

async function loadData() {
  try {
    const [gr, pr] = await Promise.all([
      chatAPI.groups().catch(() => ({ data: { code: -1, data: { groups: [] } } })),
      usersAPI.messages().catch(() => ({ data: { code: -1, data: { items: [] } } }))
    ])
    if (gr.data.code === 0) groups.value = gr.data.data.groups || []
    if (pr.data.code === 0) privates.value = pr.data.data.items || []
  } catch (e) {}
  loading.value = false
}

onMounted(() => { loadData(); pollTimer = setInterval(loadData, 30000) })
onUnmounted(() => { clearInterval(pollTimer) })
</script>

<style scoped>
.msg-page { background: #F2F4F5; min-height: 100vh; font-family: 'PingFang SC', sans-serif }

/* Header */
.msg-header { background: linear-gradient(180deg, #06D6A0 0%, #0096C7 100%); padding: 56px 0 36px }
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
.group-grid { width: 48px; height: 48px; display: grid; gap: 1px; border-radius: 8px; overflow: hidden; flex-shrink: 0 } .group-grid.grid-1 { grid-template-columns: 1fr; grid-template-rows: 1fr } .group-grid.grid-4 { grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr } .group-grid.grid-9 { grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(3, 1fr) } .grid-cell { position: relative; background: rgba(255,255,255,.15); display: flex; align-items: center; justify-content: center; font-size: 10px; color: #fff; min-width: 0; min-height: 0 } .grid-img { width: 100%; height: 100%; object-fit: cover } .grid-more { position: absolute; inset: 0; background: rgba(0,0,0,.5); color: #fff; font-size: 10px; display: flex; align-items: center; justify-content: center }
</style>
