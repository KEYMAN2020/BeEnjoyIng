<template>
  <div class="page">
    <div class="header" style="padding:12px 14px;display:flex;align-items:center;gap:12px">
      <button @click="$router.back()" style="background:none;border:none;color:#fff;font-size:20px;cursor:pointer">‹</button>
      <span style="color:#fff;font-size:18px;font-weight:700">新的朋友</span>
    </div>

    <div v-if="loading" style="text-align:center;padding:60px;color:#999">加载中...</div>

    <template v-else>
      <div v-if="requests.length === 0" style="text-align:center;padding:80px 20px;color:#999">
        <div style="font-size:48px;margin-bottom:12px">📬</div>
        <div>暂无好友申请</div>
      </div>
      <div v-else>
        <div v-for="r in requests" :key="r.request_id" class="req-item">
          <div class="req-avatar">{{ r.nickname?.[0] || '?' }}</div>
          <div class="req-info">
            <div class="req-name">{{ r.nickname }}</div>
            <div class="req-hint">请求添加你为好友</div>
          </div>
          <button v-if="r.status === 'pending'" class="req-accept" @click="handleAccept(r.request_id)">接受</button>
          <span v-else style="font-size:12px;color:#999">{{ r.status === 'accepted' ? '已添加' : '已拒绝' }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const requests = ref([])
const loading = ref(true)

async function loadRequests() {
  try {
    const res = await api.get('/users/friends/requests/pending')
    if (res.data.code === 0) requests.value = res.data.data.items || []
  } catch(e) {}
  loading.value = false
}

async function handleAccept(id) {
  try {
    const res = await api.put(`/users/friends/request/${id}`, { action: 'accept' })
    if (res.data.code === 0) loadRequests()
  } catch(e) {}
}

onMounted(async () => {
  await loadRequests()
  localStorage.setItem('last_seen_requests', String(requests.value.length))
})
</script>

<style scoped>
.header { background: linear-gradient(135deg, #FF6B35, #FF8A50); border-radius: 0 0 20px 20px; }
.req-item { display: flex; align-items: center; padding: 14px 16px; background: #fff; gap: 12px; border-bottom: 1px solid #f5f5f5; }
.req-avatar { width: 44px; height: 44px; border-radius: 8px; background: linear-gradient(135deg, #FF6B35, #FFB74D); color: #fff; font-size: 20px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.req-info { flex: 1; }
.req-name { font-size: 16px; font-weight: 600; }
.req-hint { font-size: 12px; color: #999; margin-top: 2px; }
.req-accept { background: #07C160; color: #fff; border: none; padding: 6px 16px; border-radius: 6px; font-size: 13px; cursor: pointer; }
</style>
