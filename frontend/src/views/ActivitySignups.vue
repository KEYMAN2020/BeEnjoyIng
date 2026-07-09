<template>
  <div class="signups-page">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">‹ 返回</button>
      <h1 style="flex:1;text-align:center">报名列表</h1>
      <div style="width:50px"></div>
    </div>

    <div v-if="loading" class="loading-spinner"><div class="spinner"></div></div>
    <div v-else-if="signups.length === 0" class="empty-state">暂无报名</div>
    <div v-else class="signup-list">
      <div v-for="s in signups" :key="s.id" class="signup-item">
        <div class="signup-avatar">{{ s.user?.nickname?.[0] || '?' }}</div>
        <div class="signup-info">
          <div class="signup-name">
            {{ s.user?.nickname || '未知' }}
            <span class="status-tag" :style="{ color: statusColor(s.status) }">{{ s.status_text || s.status }}</span>
          </div>
          <div class="signup-meta" v-if="s.created_at">
            {{ formatDate(s.created_at) }} 报名
          </div>
        </div>
        <button v-if="s.status === 'confirmed'" class="btn btn-sm btn-outline" @click="handleCheckin(s)">签到</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { activitiesAPI } from '@/api'

const route = useRoute()
const loading = ref(true)
const signups = ref([])

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth()+1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

function statusColor(status) {
  const map = { confirmed: '#52C41A', pending: '#FAAD14', cancelled: '#999', checked_in: '#1890FF' }
  return map[status] || '#666'
}

async function handleCheckin(signup) {
  try {
    const res = await activitiesAPI.checkin(route.params.id)
    if (res.data.code === 0) {
      signup.status = 'checked_in'
      signup.status_text = '已签到'
    }
  } catch (e) {}
}

onMounted(async () => {
  try {
    const res = await activitiesAPI.signups(route.params.id)
    if (res.data.code === 0) signups.value = res.data.data
  } catch (e) {} finally { loading.value = false }
})
</script>

<style scoped>
.signup-list { background: var(--bg-white); }
.signup-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}
.signup-avatar {
  width: 40px; height: 40px;
  border-radius: 50%;
  background: var(--primary-light);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}
.signup-info { flex: 1; }
.signup-name { font-size: 14px; display: flex; align-items: center; gap: 8px; }
.signup-meta { font-size: 12px; color: var(--text-hint); margin-top: 2px; }
.status-tag { font-size: 12px; font-weight: 500; }
.back-btn { background: none; font-size: 16px; color: var(--primary); font-weight: 500; }
</style>
