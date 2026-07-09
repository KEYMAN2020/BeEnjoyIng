<template>
  <div class="fr-page">
    <div class="fr-header">
      <button class="fr-back" @click="$router.back()">‹</button>
      <span class="fr-title">新的朋友</span>
      <div class="fr-placeholder"></div>
    </div>

    <div v-if="loading" class="fr-loading">加载中...</div>

    <template v-else>
      <div v-if="requests.length === 0" class="fr-empty">
        <div class="fr-empty-icon">📬</div>
        <div>暂无好友申请</div>
      </div>
      <div v-else class="fr-list">
        <div v-for="r in requests" :key="r.request_id" class="fr-item">
          <div class="fr-avatar">{{ (r.from_nickname || '?')[0] }}</div>
          <div class="fr-info">
            <div class="fr-name">{{ r.from_nickname }}</div>
            <div class="fr-hint">请求添加你为好友</div>
          </div>
          <button class="fr-accept" @click="handleAccept(r.request_id)">接受</button>
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
    const res = await api.put('/users/friends/request/' + id, { action: 'accept' })
    if (res.data.code === 0) loadRequests()
  } catch(e) {}
}

onMounted(() => loadRequests())
</script>

<style scoped>
.fr-page { background: #F2F4F5; min-height: 100vh }
.fr-header { background: linear-gradient(180deg, #06D6A0 0%, #0096C7 100%); padding: 48px 16px 24px; display: flex; align-items: center; border-radius: 0 0 20px 20px }
.fr-back { background: none; border: none; color: #fff; font-size: 22px; cursor: pointer; width: 36px }
.fr-title { flex: 1; text-align: center; color: #fff; font-size: 18px; font-weight: 700 }
.fr-placeholder { width: 36px }
.fr-loading { text-align: center; padding: 60px; color: #999 }
.fr-empty { text-align: center; padding: 80px 20px; color: #999 }
.fr-empty-icon { font-size: 48px; margin-bottom: 12px }
.fr-list { background: #fff; margin: 12px 16px; border-radius: 16px; overflow: hidden }
.fr-item { display: flex; align-items: center; padding: 14px 16px; gap: 12px; border-bottom: 1px solid #f5f5f5 }
.fr-item:last-child { border-bottom: none }
.fr-avatar { width: 44px; height: 44px; border-radius: 8px; background: linear-gradient(135deg, #06D6A0, #0096C7); color: #fff; font-size: 20px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0 }
.fr-info { flex: 1 }
.fr-name { font-size: 16px; font-weight: 600; color: #333 }
.fr-hint { font-size: 12px; color: #999; margin-top: 2px }
.fr-accept { background: #06D6A0; color: #fff; border: none; padding: 6px 16px; border-radius: 14px; font-size: 13px; cursor: pointer; font-weight: 600 }
.fr-accept:active { opacity: .8 }
</style>
