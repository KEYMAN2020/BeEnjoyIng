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
          <div class="msg-avatar">
            <img v-if="item._avatar" :src="item._avatar" />
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

const mergedList = computed(() => {
  const list = []
  if (Array.isArray(groups.value)) {
    groups.value.forEach(g => {
      list.push({
        _key: 'g-' + g.id, _type: 'group', _name: g.name || '群聊',
        _avatar: g.avatar || '', _initial: (g.name || '群')[0],
        _avatarBg: {}, _preview: g.last_message || '暂无消息',
        _time: formatTime(g.last_message_at), _unread: g.unread_count || 0, _targetId: g.id
      })
    })
  }
  if (Array.isArray(privates.value)) {
    privates.value.forEach(p => {
      const other = p.other_user || {}
      list.push({
        _key: 'p-' + (other.user_id || p.message_id), _type: 'private',
        _name: other.nickname || '用户', _avatar: other.avatar_url || '',
        _initial: (other.nickname || '?')[0], _avatarBg: {},
        _preview: p.content || '暂无消息', _time: formatTime(p.created_at),
        _unread: (other.user_id && !p.is_read) ? 1 : 0, _targetId: other.user_id
      })
    })
  }
  list.sort((a, b) => (b._time || '').localeCompare(a._time || ''))
  return list
})

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts); const now = new Date()
  if (d.toDateString() === now.toDateString()) return d.toTimeString().slice(0, 5)
  return (d.getMonth() + 1) + '/' + d.getDate()
}

function onMsgClick(item) {
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
</style>
