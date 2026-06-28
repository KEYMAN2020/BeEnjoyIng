<template>
  <div class="detail-page">
    <!-- Header -->
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">‹ 返回</button>
      <h1 style="flex:1;text-align:center;font-size:16px">活动详情</h1>
      <div style="width:50px"></div>
    </div>

    <div v-if="loading" class="loading-spinner" style="padding-top:80px"><div class="spinner"></div></div>

    <template v-else-if="activity">
      <!-- Status Banner -->
      <div class="status-banner" :style="{ background: activity.status_color + '1a', color: activity.status_color }">
        {{ activity.status_text }}
      </div>

      <!-- Title -->
      <div class="detail-title">{{ activity.title }}</div>

      <!-- Meta Info -->
      <div class="detail-meta">
        <div class="meta-item" v-if="activity.captain">
          <span>👨‍💼 队长</span>
          <span>{{ activity.captain.nickname }}</span>
        </div>
        <div class="meta-item">
          <span>📅 时间</span>
          <span>{{ formatDate(activity.start_time) }}</span>
        </div>
        <div class="meta-item">
          <span>📍 地点</span>
          <span>{{ activity.city || activity.location_name || '待定' }}{{ activity.district ? ' ' + activity.district : '' }}</span>
        </div>
        <div class="meta-item" v-if="activity.distance_text">
          <span>📏 距离</span>
          <span>{{ activity.distance_text }}</span>
        </div>
        <div class="meta-item">
          <span>👥 人数</span>
          <span>{{ activity.current_participants || 0 }} / {{ activity.max_participants || '不限' }}</span>
        </div>
        <div class="meta-item" v-if="activity.category">
          <span>🏷️ 分类</span>
          <span>{{ activity.category }}</span>
        </div>
      </div>

      <!-- Description -->
      <div class="detail-section" v-if="activity.description">
        <h3>活动介绍</h3>
        <p>{{ activity.description }}</p>
      </div>

      <!-- Weather -->
      <div class="detail-section" v-if="weather">
        <h3>🌤️ 当地天气</h3>
        <div class="weather-info">
          <span>{{ weather.day_temp }}°C</span>
          <span>{{ weather.day_weather }}</span>
        </div>
      </div>

      <!-- Albums -->
      <div class="detail-section" v-if="albums.length > 0">
        <h3>📷 活动相册</h3>
        <div class="album-grid">
          <img v-for="photo in albums" :key="photo.id" :src="photo.image_url" :alt="photo.description" />
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="detail-actions" v-if="activity.status !== 'closed' && activity.status_text !== '已结束' && activity.status_text !== '已结束' && activity.status_text !== '已解散'">
        <button v-if="canSignup && !hasSignedUp && !activity.is_captain" class="btn btn-primary btn-block" @click="handleSignup">立即报名</button>
        <button v-if="hasSignedUp && !activity.is_captain" class="btn btn-outline btn-block" @click="handleCancel">取消报名</button>
        <button v-if="activity.is_captain && activity.status === 'open'" class="btn btn-block" :style="isEnded ? {background:'#52C41A',color:'#fff'} : {background:'#ccc',color:'#999'}" @click="isEnded ? handleComplete() : null" :disabled="!isEnded">完成活动{{ !isEnded ? ' (需等活动结束)' : '' }}</button>
        <button v-if="activity.is_captain && activity.status === 'open'" class="btn btn-outline btn-block" @click="handleDisband">解散活动</button>
        <button v-if="!activity.is_captain" class="btn btn-outline btn-sm" @click="handleFavorite" style="margin-top:8px">
          {{ activity.is_favorited ? '❤️ 已收藏' : '🤍 收藏' }}
        </button>
      </div>

      <!-- Closed Label -->
      <div v-if="activity.status_text === '已结束' || activity.status_text === '已结束' || activity.status_text === '已解散'" style="padding:16px;text-align:center;color:#999;font-size:14px">
        <div class="closed-badge">{{ activity.status_text }}</div>
      </div>

      <!-- Reviews -->
      <div class="detail-section" v-if="reviews.length > 0">
        <h3>💬 评价 ({{ reviews.length }})</h3>
        <div v-for="r in reviews" :key="r.id" class="review-item">
          <div class="review-header">
            <span class="review-user">{{ r.user?.nickname || '匿名' }}</span>
            <span class="review-stars">⭐ {{ r.rating }}</span>
          </div>
          <p v-if="r.content">{{ r.content }}</p>
        </div>
      </div>

      <div style="height:40px"></div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { activitiesAPI } from '@/api'

const route = useRoute()
const auth = useAuthStore()

const loading = ref(true)
const activity = ref(null)
const weather = ref(null)
const albums = ref([])
const reviews = ref([])

const canSignup = computed(() => activity.value?.status === 'open')
const isEnded = computed(() => {
  if (!activity.value?.end_time) return false
  return new Date(activity.value.end_time) < new Date()
})
const hasSignedUp = computed(() => activity.value?.signup_status)
const isLoggedIn = computed(() => auth.isLoggedIn)

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

async function loadActivity() {
  loading.value = true
  try {
    const res = await activitiesAPI.detail(route.params.id)
    if (res.data.code === 0) {
      activity.value = res.data.data.activity || res.data.data
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadWeather() {
  try {
    const res = await activitiesAPI.weather(route.params.id)
    if (res.data.code === 0) weather.value = res.data.data.weather || res.data.data
  } catch (e) {}
}

async function loadAlbums() {
  try {
    const res = await activitiesAPI.albums(route.params.id)
    if (res.data.code === 0) albums.value = res.data.data.photos || res.data.data
  } catch (e) {}
}

async function loadReviews() {
  try {
    const res = await activitiesAPI.signups(route.params.id)
    if (res.data.code === 0) reviews.value = (res.data.data || []).filter(s => s.rating)
  } catch (e) {}
}

async function handleSignup() {
  if (!isLoggedIn.value) return
  try {
    const res = await activitiesAPI.signup(route.params.id)
    if (res.data.code === 0) {
      activity.value.signup_status = 'confirmed'
      activity.value.current_participants = (activity.value.current_participants || 0) + 1
    }
  } catch (e) {}
}

async function handleCancel() {
  try {
    const res = await activitiesAPI.cancel(route.params.id)
    if (res.data.code === 0) {
      activity.value.signup_status = null
      activity.value.current_participants = Math.max(0, (activity.value.current_participants || 0) - 1)
    }
  } catch (e) {}
}

async function handleComplete() {
  try {
    const res = await activitiesAPI.complete(route.params.id)
    if (res.data.code === 0) {
      activity.value.status = 'ended'
      activity.value.status_text = '已结束'
      activity.value.status_color = '#666'
    }
  } catch (e) {}
}

async function handleDisband() {
  try {
    const res = await activitiesAPI.disband(route.params.id)
    if (res.data.code === 0) {
      activity.value.status = 'disbanded'
      activity.value.status_text = '已解散'
      activity.value.status_color = '#999'
    }
  } catch (e) {}
}

async function handleFavorite() {
  try {
    if (activity.value.is_favorited) {
      await activitiesAPI.unfavorite(route.params.id)
      activity.value.is_favorited = false
    } else {
      await activitiesAPI.favorite(route.params.id)
      activity.value.is_favorited = true
    }
  } catch (e) {}
}

onMounted(() => {
  loadActivity()
  loadWeather()
  loadAlbums()
  loadReviews()
})
</script>

<style scoped>
.detail-page {
  background: var(--bg-white);
  min-height: 100vh;
}
.back-btn {
  background: none;
  font-size: 16px;
  color: var(--primary);
  font-weight: 500;
}
.status-banner {
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  text-align: center;
}
.detail-title {
  padding: 16px;
  font-size: 20px;
  font-weight: 700;
  line-height: 1.4;
}
.detail-meta {
  padding: 0 16px 16px;
}
.meta-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 14px;
  border-bottom: 1px solid var(--border);
}
.meta-item span:first-child {
  color: var(--text-hint);
}
.detail-section {
  padding: 16px;
  border-top: 8px solid var(--bg);
}
.detail-section h3 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 10px;
}
.detail-section p {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
}
.weather-info {
  display: flex;
  gap: 16px;
  font-size: 16px;
}
.album-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}
.album-grid img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  border-radius: 6px;
}
.detail-actions {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.review-item {
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}
.review-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}
.review-user {
  font-weight: 500;
  font-size: 14px;
}
.review-stars {
  font-size: 13px;
  color: #faad14;
}
.review-item p {
  font-size: 13px;
  color: var(--text-secondary);
}
.closed-badge { margin: 12px 16px; padding: 12px 0; text-align: center; background: #e0e0e0; color: #888; border-radius: 12px; font-size: 14px; font-weight: 600; }
</style>
