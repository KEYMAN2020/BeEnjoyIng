<template>
  <div class="ad-page">
    <!-- Header -->
    <div class="ad-header">
      <button class="ad-back" @click="$router.back()">‹</button>
      <span class="ad-h-title">活动详情</span>
      <div class="ad-h-right"></div>
    </div>

    <div v-if="loading" class="ad-loading">
      <div class="spinner"></div>
    </div>

    <template v-else-if="activity">
      <!-- Card 1: Title + Status + Meta -->
      <div class="ad-card">
        <!-- Status chip -->
        <div class="ad-status" :style="{ background: activity.status_color + '18', color: activity.status_color }">
          {{ activity.status_text }}
        </div>

        <!-- Title -->
        <div class="ad-title">{{ activity.title }}</div>

        <!-- Meta grid (2列) -->
        <div class="ad-meta-grid">
          <div class="ad-meta" v-if="activity.captain">
            <span class="ad-meta-icon">👨‍💼</span>
            <span class="ad-meta-label">队长</span>
            <span class="ad-meta-val">{{ activity.captain.nickname }}</span>
          </div>
          <div class="ad-meta">
            <span class="ad-meta-icon">📅</span>
            <span class="ad-meta-label">时间</span>
            <span class="ad-meta-val">{{ formatDate(activity.start_time) }}</span>
          </div>
          <div class="ad-meta">
            <span class="ad-meta-icon">📍</span>
            <span class="ad-meta-label">地点</span>
            <span class="ad-meta-val">{{ activity.city || activity.location_name || '待定' }}{{ activity.district ? ' ' + activity.district : '' }}</span>
          </div>
          <div class="ad-meta">
            <span class="ad-meta-icon">👥</span>
            <span class="ad-meta-label">人数</span>
            <span class="ad-meta-val">{{ activity.current_participants || 0 }} / {{ activity.max_participants || '不限' }}</span>
          </div>
        </div>
      </div>

      <!-- Card 2: Description -->
      <div class="ad-card" v-if="activity.description">
        <h3 class="ad-card-title">活动介绍</h3>
        <p class="ad-card-text">{{ activity.description }}</p>
      </div>

      <!-- Card 3: Weather -->
      <div class="ad-card" v-if="weather">
        <h3 class="ad-card-title">🌤️ 当地天气</h3>
        <div class="ad-weather">
          <span class="ad-weather-temp">{{ weather.day_temp }}°C</span>
          <span class="ad-weather-desc">{{ weather.day_weather }}</span>
        </div>
      </div>

      <!-- Card 4: Albums -->
      <div class="ad-card">
        <div class="ad-card-header">
          <h3 class="ad-card-title">📷 活动相册（{{ albums.length }}）</h3>
          <button v-if="activity.is_captain && activity.status !== 'closed'" class="ad-album-upload" @click="triggerAlbumUpload">
            <span v-if="uploadingAlbum">上传中...</span>
            <span v-else>+ 添加照片</span>
          </button>
        </div>
        <input ref="albumInput" type="file" accept="image/*" multiple style="display:none" @change="handleAlbumUpload" />
        <div class="ad-albums" v-if="albums.length > 0">
          <img v-for="photo in albums" :key="photo.id" :src="photo.image_url" :alt="photo.description" />
        </div>
        <div v-else class="ad-albums-empty">暂无照片</div>
      </div>

      <!-- Card 5: Action Buttons (if active) -->
      <div class="ad-card ad-card-actions" v-if="activity.status !== 'closed' && activity.status_text !== '已结束' && activity.status_text !== '已解散'">
        <button v-if="canSignup && !hasSignedUp && !activity.is_captain" class="ad-btn ad-btn-primary" @click="handleSignup">立即报名</button>
        <button v-if="hasSignedUp && !activity.is_captain" class="ad-btn ad-btn-outline" @click="handleCancel">取消报名</button>
        <button v-if="activity.is_captain && activity.status === 'open'" class="ad-btn" :class="isEnded ? 'ad-btn-success' : 'ad-btn-disabled'" @click="isEnded ? handleComplete() : null" :disabled="!isEnded">完成活动{{ !isEnded ? '（活动结束后可用）' : '' }}</button>
        <button v-if="activity.is_captain && activity.status === 'open'" class="ad-btn ad-btn-outline" @click="handleDisband">解散活动</button>
      </div>

      <!-- Card 6: Favorite -->
      <div class="ad-card ad-card-fav">
        <button class="ad-fav-btn" @click="handleFavorite">
          <span :class="activity.is_favorited ? 'ad-fav-on' : 'ad-fav-off'">{{ activity.is_favorited ? '❤️ 已收藏' : '🤍 收藏' }}</span>
        </button>
      </div>

      <!-- Card 7: Closed badge -->
      <div class="ad-card ad-card-closed" v-if="activity.status_text === '已结束' || activity.status_text === '已解散'">
        <div class="ad-closed">{{ activity.status_text }}</div>
      </div>

      <!-- Card 8: Reviews -->
      <div class="ad-card" v-if="reviews.length > 0">
        <h3 class="ad-card-title">💬 评价（{{ reviews.length }}）</h3>
        <div v-for="r in reviews" :key="r.id" class="ad-review">
          <div class="ad-review-top">
            <span class="ad-review-user">{{ r.user?.nickname || '匿名' }}</span>
            <span class="ad-review-stars">⭐ {{ r.rating }}</span>
          </div>
          <p class="ad-review-text" v-if="r.content">{{ r.content }}</p>
        </div>
      </div>

      <div style="height: 60px"></div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { activitiesAPI } from '@/api'
import { uploadAPI } from '@/api'

const route = useRoute()
const auth = useAuthStore()

const loading = ref(true)
const activity = ref(null)
const weather = ref(null)
const albums = ref([])
const albumInput = ref(null)
const uploadingAlbum = ref(false)
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
      activity.value = res.data.data?.activity || res.data.data
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
    if (res.data.code === 0) weather.value = res.data.data?.weather || res.data.data
  } catch (e) {}
}

async function loadAlbums() {
  try {
    const res = await activitiesAPI.albums(route.params.id)
    if (res.data.code === 0) albums.value = res.data.data?.photos || res.data.data
  } catch (e) {}
}

function triggerAlbumUpload() { albumInput.value?.click() }

async function handleAlbumUpload(e) {
  const files = e.target.files
  if (!files.length) return
  uploadingAlbum.value = true
  for (const file of files) {
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await uploadAPI.album(fd)
      if (res.data?.code === 0) {
        await activitiesAPI.uploadPhoto(route.params.id, { image_url: res.data.data.avatar_url })
      }
    } catch (e) {}
  }
  uploadingAlbum.value = false
  await loadAlbums()
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
.ad-page { background: #F2F4F5; min-height: 100vh }

/* Header */
.ad-header { background: linear-gradient(180deg, #06D6A0 0%, #0096C7 100%); padding: 48px 16px 20px; display: flex; align-items: center; border-radius: 0 0 20px 20px }
.ad-back { background: none; border: none; color: #fff; font-size: 22px; cursor: pointer; width: 36px; line-height: 1 }
.ad-h-title { flex: 1; text-align: center; color: #fff; font-size: 18px; font-weight: 700 }
.ad-h-right { width: 36px }

/* Loading */
.ad-loading { padding-top: 80px; text-align: center }
.spinner { width: 32px; height: 32px; border: 3px solid #E8F8F5; border-top-color: #06D6A0; border-radius: 50%; margin: 0 auto; animation: spin 0.6s linear infinite }
@keyframes spin { to { transform: rotate(360deg) } }

/* Cards */
.ad-card { background: #fff; margin: 12px 16px; border-radius: 16px; padding: 16px }

/* Status chip */
.ad-status { display: inline-block; padding: 4px 12px; border-radius: 10px; font-size: 12px; font-weight: 600; margin-bottom: 8px }

/* Title */
.ad-title { font-size: 20px; font-weight: 700; color: #222; line-height: 1.4; margin-bottom: 16px }

/* Meta grid: 2 columns */
.ad-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px 8px }
.ad-meta { display: flex; align-items: center; gap: 6px; font-size: 13px }
.ad-meta-icon { font-size: 14px }
.ad-meta-label { color: #999; min-width: 28px }
.ad-meta-val { color: #333; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap }

/* Card title */
.ad-card-title { font-size: 15px; font-weight: 600; color: #333; margin-bottom: 10px }

/* Card text */
.ad-card-text { font-size: 14px; line-height: 1.6; color: #666 }

/* Weather */
.ad-weather { display: flex; gap: 16px; align-items: center }
.ad-weather-temp { font-size: 28px; font-weight: 700; color: #06D6A0 }
.ad-weather-desc { font-size: 14px; color: #666 }

/* Albums */
.ad-albums { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px }
.ad-albums img { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 8px }
.ad-albums-empty { text-align: center; color: #999; font-size: 13px; padding: 20px 0 }
.ad-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px }
.ad-album-upload { background: #E8F8F5; color: #06D6A0; border: 1px dashed #06D6A0; border-radius: 8px; padding: 4px 12px; font-size: 13px; cursor: pointer }

/* Buttons */
.ad-card-actions { display: flex; flex-direction: column; gap: 10px }
.ad-btn { width: 100%; padding: 14px; border: none; border-radius: 14px; font-size: 16px; font-weight: 600; cursor: pointer }
.ad-btn-primary { background: linear-gradient(135deg, #06D6A0, #0096C7); color: #fff }
.ad-btn-outline { background: #fff; color: #06D6A0; border: 2px solid #06D6A0 }
.ad-btn-success { background: #52C41A; color: #fff }
.ad-btn-disabled { background: #E8E8E8; color: #999 }
.ad-btn:active { opacity: .85 }

/* Favorite */
.ad-card-fav { text-align: center }
.ad-fav-btn { background: none; border: none; cursor: pointer; padding: 4px 12px }
.ad-fav-on { color: #FF6B6B; font-size: 15px }
.ad-fav-off { color: #999; font-size: 15px }

/* Closed */
.ad-card-closed { text-align: center }
.ad-closed { color: #999; font-size: 14px; font-weight: 500 }

/* Reviews */
.ad-review { padding: 12px 0; border-bottom: 1px solid #f0f0f0 }
.ad-review:last-child { border-bottom: none }
.ad-review-top { display: flex; justify-content: space-between; margin-bottom: 4px }
.ad-review-user { font-weight: 600; font-size: 14px; color: #333 }
.ad-review-stars { font-size: 13px; color: #FAAD14 }
.ad-review-text { font-size: 13px; color: #666; line-height: 1.5 }
</style>
