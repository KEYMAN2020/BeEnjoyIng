<template>
  <div class="ad-page">
    <div class="ad-header">
      <button class="ad-back" @click="goBack">←</button>
      <span class="ad-header-title">活动详情</span>
      <button class="ad-fav" @click="toggleFavorite">{{ activity.is_favorited ? '★' : '☆' }}</button>
    </div>
    <div v-if="loading" class="ad-loading"><div class="ad-spinner"></div></div>
    <div v-else-if="error" class="ad-error">
      <div class="ad-error-icon">😢</div>
      <p>{{ error }}</p>
      <button class="ad-retry" @click="fetchDetail">重试</button>
    </div>
    <template v-else-if="activity">
      <div class="ad-cover" v-if="activity.cover_image">
        <img :src="activity.cover_image" @error="e => e.target.style.display='none'" />
      </div>
      <div class="ad-card ad-title-card">
        <div class="ad-status" :style="{ color: activity.status_color, background: (activity.status_color||'#999')+'18' }">{{ activity.status_text }}</div>
        <h1 class="ad-title">{{ activity.title }}</h1>
        <div class="ad-tags" v-if="activity.tags && activity.tags.length">
          <span v-for="tag in activity.tags" :key="tag.id" class="ad-tag">{{ tag.name }}</span>
        </div>
      </div>
      <div class="ad-card">
        <div class="ad-info-row">
          <span class="ad-info-icon">📅</span>
          <div class="ad-info-content">
            <div class="ad-info-label">活动时间</div>
            <div class="ad-info-value">{{ formatDateTime(activity.start_time) }} ~ {{ formatDateTime(activity.end_time) }}</div>
            <div class="ad-info-sub" v-if="activity.signup_deadline">报名截止：{{ formatDateTime(activity.signup_deadline) }}</div>
          </div>
        </div>
        <div class="ad-info-row">
          <span class="ad-info-icon">📍</span>
          <div class="ad-info-content">
            <div class="ad-info-label">活动地点</div>
            <div class="ad-info-value">{{ activity.location_name || '待定' }}</div>
            <div class="ad-info-sub" v-if="activity.location_address">{{ activity.location_address }}</div>
            <div class="ad-info-sub" v-if="activity.city">{{ activity.city }}{{ activity.district ? ' ' + activity.district : '' }}</div>
          </div>
        </div>
        <div class="ad-info-row">
          <span class="ad-info-icon">👥</span>
          <div class="ad-info-content">
            <div class="ad-info-label">参与人数</div>
            <div class="ad-info-value">{{ activity.current_participants || 0 }} / {{ activity.max_participants || '不限' }} 人</div>
            <div class="ad-info-sub" v-if="activity.min_participants">最少 {{ activity.min_participants }} 人成团</div>
          </div>
        </div>
        <div class="ad-info-row" v-if="activity.price > 0">
          <span class="ad-info-icon">💰</span>
          <div class="ad-info-content">
            <div class="ad-info-label">活动费用</div>
            <div class="ad-info-value">¥{{ activity.price }}</div>
          </div>
        </div>
        <div class="ad-info-row" v-if="activity.distance">
          <span class="ad-info-icon">📏</span>
          <div class="ad-info-content">
            <div class="ad-info-label">距离</div>
            <div class="ad-info-value">{{ activity.distance.toFixed(1) }} km</div>
          </div>
        </div>
      </div>
      <div class="ad-card" v-if="activity.description">
        <div class="ad-card-title">活动介绍</div>
        <div class="ad-desc">{{ activity.description }}</div>
      </div>
      <div class="ad-card" v-if="activity.photos && activity.photos.length">
        <div class="ad-card-title">活动相册</div>
        <div class="ad-photos">
          <img v-for="(photo, i) in activity.photos" :key="i" :src="photo" class="ad-photo" @error="e => e.target.style.display='none'" />
        </div>
      </div>
      <div class="ad-card" v-if="activity.captain">
        <div class="ad-card-title">活动发起人</div>
        <div class="ad-captain" @click="goProfile(activity.captain.user_id || activity.captain.id)">
          <div class="ad-captain-avatar">
            <img v-if="activity.captain.avatar_url" :src="activity.captain.avatar_url" @error="e => e.target.style.display='none'" />
            <span v-else>{{ (activity.captain.nickname || '?')[0] }}</span>
          </div>
          <div class="ad-captain-info">
            <div class="ad-captain-name">{{ activity.captain.nickname }}</div>
            <div class="ad-captain-phone" v-if="activity.captain.phone && activity.is_captain">{{ activity.captain.phone }}</div>
          </div>
          <span class="ad-captain-arrow">›</span>
        </div>
      </div>
      <div class="ad-action-bar">
        <template v-if="activity.is_captain">
          <button class="ad-btn ad-btn-disabled" disabled>我发起的活动</button>
        </template>
        <template v-else-if="activity.status === 'open'">
          <button v-if="!activity.my_status" class="ad-btn ad-btn-primary" :disabled="actionLoading" @click="doSignup">
            {{ actionLoading ? '报名中...' : '立即报名' }}
          </button>
          <button v-else class="ad-btn ad-btn-cancel" :disabled="actionLoading" @click="doCancelSignup">
            {{ actionLoading ? '取消中...' : '取消报名' }}
          </button>
        </template>
        <template v-else>
          <button class="ad-btn ad-btn-disabled" disabled>活动{{ activity.status_text }}</button>
        </template>
      </div>
      <div style="height:80px"></div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { activitiesAPI } from '@/api'

const route = useRoute()
const router = useRouter()
const activity = ref(null)
const loading = ref(true)
const error = ref('')
const actionLoading = ref(false)

function goBack() { router.back() }
function goProfile(id) { if (id) router.push('/profile/' + id) }

function formatDateTime(d) {
  if (!d) return ''
  const dt = new Date(d)
  if (isNaN(dt)) return d
  return (dt.getMonth()+1) + '月' + dt.getDate() + '日 ' + String(dt.getHours()).padStart(2,'0') + ':' + String(dt.getMinutes()).padStart(2,'0')
}

async function fetchDetail() {
  loading.value = true
  error.value = ''
  try {
    const res = await activitiesAPI.detail(route.params.id)
    const d = res.data || res
    if (d.code === 0) {
      activity.value = d.data?.activity || d.data || null
    } else {
      error.value = d.message || '加载失败'
    }
  } catch(e) {
    error.value = '网络错误，请重试'
  } finally {
    loading.value = false
  }
}

async function doSignup() {
  actionLoading.value = true
  try {
    const res = await activitiesAPI.signup(route.params.id)
    const d = res.data || res
    if (d.code === 0) {
      activity.value.my_status = 'registered'
      activity.value.current_participants = (activity.value.current_participants || 0) + 1
      alert('报名成功！')
    } else {
      alert(d.message || '报名失败')
    }
  } catch(e) {
    alert('网络错误')
  } finally {
    actionLoading.value = false
  }
}

async function doCancelSignup() {
  if (!confirm('确定取消报名？')) return
  actionLoading.value = true
  try {
    const res = await activitiesAPI.cancelSignup(route.params.id)
    const d = res.data || res
    if (d.code === 0) {
      activity.value.my_status = null
      activity.value.current_participants = Math.max((activity.value.current_participants || 0) - 1, 0)
      alert('已取消报名')
    } else {
      alert(d.message || '取消失败')
    }
  } catch(e) {
    alert('网络错误')
  } finally {
    actionLoading.value = false
  }
}

async function toggleFavorite() {
  if (!activity.value) return
  try {
    if (activity.value.is_favorited) {
      await activitiesAPI.unfavorite(route.params.id)
      activity.value.is_favorited = false
    } else {
      await activitiesAPI.favorite(route.params.id)
      activity.value.is_favorited = true
    }
  } catch(e) {
    alert('操作失败')
  }
}

onMounted(() => { fetchDetail() })
</script>

<style scoped>
.ad-page { background: #F2F4F5; min-height: 100vh; font-family: 'PingFang SC', sans-serif }
.ad-header { display: flex; align-items: center; padding: 12px 16px; background: linear-gradient(180deg, #06D6A0 0%, #0096C7 100%); position: sticky; top: 0; z-index: 10 }
.ad-back { background: rgba(255,255,255,.25); border: 1px solid rgba(255,255,255,.4); color: #fff; width: 32px; height: 32px; border-radius: 50%; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center }
.ad-header-title { flex: 1; text-align: center; color: #fff; font-size: 17px; font-weight: 700 }
.ad-fav { background: rgba(255,255,255,.25); border: 1px solid rgba(255,255,255,.4); color: #FFD700; width: 32px; height: 32px; border-radius: 50%; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center }
.ad-loading { text-align: center; padding: 80px 0 }
.ad-spinner { width: 32px; height: 32px; border: 3px solid #E8F8F5; border-top-color: #06D6A0; border-radius: 50%; margin: 0 auto; animation: ad-spin .8s linear infinite }
@keyframes ad-spin { to { transform: rotate(360deg) } }
.ad-error { text-align: center; padding: 80px 20px; color: #999 }
.ad-error-icon { font-size: 48px; margin-bottom: 12px }
.ad-error p { font-size: 15px; margin-bottom: 16px }
.ad-retry { padding: 8px 24px; background: #06D6A0; color: #fff; border: none; border-radius: 20px; font-size: 14px; cursor: pointer }
.ad-cover { width: 100%; height: 200px; overflow: hidden }
.ad-cover img { width: 100%; height: 100%; object-fit: cover }
.ad-card { background: #fff; margin: 8px 16px; border-radius: 14px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,.04) }
.ad-card-title { font-size: 15px; font-weight: 700; color: #333; margin-bottom: 12px }
.ad-title-card { position: relative }
.ad-status { display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: 600; margin-bottom: 8px }
.ad-title { font-size: 20px; font-weight: 700; color: #2D2D2D; line-height: 1.4; margin: 0 }
.ad-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px }
.ad-tag { background: #E8F8F5; color: #06D6A0; padding: 3px 10px; border-radius: 10px; font-size: 12px }
.ad-info-row { display: flex; align-items: flex-start; padding: 12px 0; border-bottom: 1px solid #f5f5f5 }
.ad-info-row:last-child { border-bottom: none }
.ad-info-icon { width: 28px; text-align: center; font-size: 18px; flex-shrink: 0 }
.ad-info-content { flex: 1 }
.ad-info-label { font-size: 12px; color: #999; margin-bottom: 2px }
.ad-info-value { font-size: 14px; color: #2D2D2D; font-weight: 500 }
.ad-info-sub { font-size: 12px; color: #999; margin-top: 2px }
.ad-desc { font-size: 14px; color: #555; line-height: 1.7; white-space: pre-wrap }
.ad-photos { display: flex; gap: 8px; overflow-x: auto; -webkit-overflow-scrolling: touch }
.ad-photo { width: 120px; height: 120px; object-fit: cover; border-radius: 10px; flex-shrink: 0 }
.ad-captain { display: flex; align-items: center; cursor: pointer }
.ad-captain:active { opacity: .8 }
.ad-captain-avatar { width: 44px; height: 44px; border-radius: 50%; background: #E8F8F5; color: #06D6A0; font-size: 20px; font-weight: 700; display: flex; align-items: center; justify-content: center; overflow: hidden; flex-shrink: 0 }
.ad-captain-avatar img { width: 100%; height: 100%; object-fit: cover }
.ad-captain-info { flex: 1; margin-left: 12px }
.ad-captain-name { font-size: 15px; font-weight: 600; color: #2D2D2D }
.ad-captain-phone { font-size: 12px; color: #999; margin-top: 2px }
.ad-captain-arrow { color: #ccc; font-size: 18px }
.ad-action-bar { position: fixed; bottom: 0; left: 0; right: 0; background: #fff; padding: 12px 16px; box-shadow: 0 -2px 12px rgba(0,0,0,.08); z-index: 100 }
.ad-btn { width: 100%; padding: 14px; border: none; border-radius: 14px; font-size: 16px; font-weight: 600; cursor: pointer }
.ad-btn-primary { background: linear-gradient(135deg, #06D6A0, #0096C7); color: #fff }
.ad-btn-primary:active { opacity: .9 }
.ad-btn-primary:disabled { opacity: .5 }
.ad-btn-cancel { background: #fff; color: #ff4d4f; border: 1px solid #ff4d4f }
.ad-btn-cancel:active { background: #fff5f5 }
.ad-btn-cancel:disabled { opacity: .5 }
.ad-btn-disabled { background: #f0f0f0; color: #999; cursor: not-allowed }
</style>
