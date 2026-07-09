<template>
  <div class="wx-grouplist">
    <!-- 顶部导航 -->
    <div class="wx-navbar">
      <button class="wx-back-btn" @click="$router.back()">‹</button>
      <span class="wx-title">群聊</span>
      <span class="wx-nav-right"></span>
    </div>

    <!-- 群聊列表 -->
    <div class="wx-group-list">
      <div v-if="loading" class="wx-loading">加载中...</div>
      <div v-else-if="groups.length === 0" class="wx-empty">
        <div class="wx-empty-icon">👥</div>
        <p>暂无群聊</p>
        <p class="wx-empty-hint">创建或加入活动后会自动生成群聊</p>
      </div>
      <div
        v-else
        v-for="g in groups"
        :key="g.group_id"
        class="wx-group-item"
        @click="$router.push('/messages/' + g.group_id)"
      >
        <div class="wx-group-avatar">
          <img v-if="g.avatar_url" :src="g.avatar_url" />
          <span v-else>{{ (g.name || '群')[0] }}</span>
        </div>
        <div class="wx-group-info">
          <div class="wx-group-name">{{ g.name || '群聊' }}</div>
          <div class="wx-group-preview">{{ g.last_message || '暂无消息' }}</div>
        </div>
        <div class="wx-group-meta">
          <div class="wx-group-time">{{ formatTime(g.last_time) }}</div>
          <div v-if="g.unread_count > 0" class="wx-group-badge">
            {{ g.unread_count > 99 ? '99+' : g.unread_count }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { chatAPI } from '@/api'

const groups = ref([])
const loading = ref(true)

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

async function loadGroups() {
  loading.value = true
  try {
    const res = await chatAPI.groups()
    if (res.data.code === 0) {
      groups.value = res.data.groups || []
    }
  } catch (e) {
    console.error('loadGroups error', e)
  }
  loading.value = false
}

onMounted(() => {
  loadGroups()
})
</script>

<style scoped>
.wx-grouplist { background: #fff; min-height: 100vh; padding-bottom: 60px; }

/* === 顶部导航 === */
.wx-navbar {
  position: sticky; top: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  height: 44px; background: #EDEDED; padding: 0 16px;
  border-bottom: 0.5px solid #D9D9D9;
}
.wx-back-btn {
  background: none; border: none; font-size: 28px; color: #07C160;
  cursor: pointer; padding: 0 8px 0 0; line-height: 1;
}
.wx-title { font-size: 17px; font-weight: 600; color: #111; }
.wx-nav-right { width: 40px; }

/* === 群聊列表 === */
.wx-group-list { background: #fff; }

.wx-group-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px; cursor: pointer; position: relative;
}
.wx-group-item::after {
  content: ''; position: absolute; left: 68px; right: 0; bottom: 0;
  height: 0.5px; background: #E5E5E5;
}
.wx-group-item:active { background: #F5F5F5; }

.wx-group-avatar {
  width: 48px; height: 48px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; color: #fff; overflow: hidden; flex-shrink: 0;
  background: linear-gradient(135deg, #07C160, #10d56a);
}
.wx-group-avatar img { width: 100%; height: 100%; object-fit: cover; }

.wx-group-info { flex: 1; overflow: hidden; }
.wx-group-name { font-size: 16px; color: #111; font-weight: 400; }
.wx-group-preview { font-size: 14px; color: #999; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.wx-group-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; flex-shrink: 0; }
.wx-group-time { font-size: 12px; color: #999; }
.wx-group-badge {
  background: #FA5151; color: #fff; font-size: 11px;
  min-width: 18px; height: 18px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  padding: 0 5px; font-weight: 600;
}

/* === 空状态 === */
.wx-loading { text-align: center; padding: 40px 0; color: #999; font-size: 14px; }
.wx-empty { text-align: center; padding: 60px 0; color: #999; }
.wx-empty-icon { font-size: 48px; margin-bottom: 12px; }
.wx-empty-hint { font-size: 13px; margin-top: 4px; }
</style>
