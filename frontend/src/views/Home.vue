<template>
  <div class="home-page">
    <!-- ═══ Teal Header ═══ -->
    <div class="h-header">
      <div class="h-header-row">
        <span class="h-title">发现活动</span>
        <button class="h-filter-btn" @click="showFilters = !showFilters">{{ showFilters ? '收起' : '🔍 筛选' }}</button>
      </div>
    </div>

    <!-- ═══ Category Tabs ═══ -->
    <div class="h-tabs-wrap">
      <div class="h-tabs">
        <button :class="{ on: activeTab==='all' }" @click="activeTab='all'; fetchActivities()">全部</button>
        <button :class="{ on: activeTab==='nearby' }" @click="activeTab='nearby'; fetchNearby()">📍 附近</button>
        <button v-for="cat in categories" :key="cat.id" :class="{ on: activeTab===cat.name }" @click="activeTab=cat.name; filterByCategory(cat.name)">{{ cat.name }}</button>
      </div>
    </div>

    <!-- ═══ Filter Panel ═══ -->
    <div v-if="showFilters" class="h-filters">
      <div class="h-frow">
        <label class="h-flabel">📅 日期</label>
        <input type="date" v-model="filters.date" class="h-finput" @change="fetchActivities" />
      </div>
      <!-- 标签功能暂不开放 -->
      <!--
      <div class="h-frow">
        <label class="h-flabel">🏷️ 标签</label>
        <div class="h-ftags">
          <span v-for="tag in availableTags" :key="tag" class="h-ftag" :class="{ on: filters.tags.includes(tag) }" @click="toggleTag(tag)">{{ tag }}</span>
        </div>
      </div>
      -->
    </div>

    <!-- ═══ Hotspot Section ═══ -->
    <div class="h-hotspot">
      <div class="h-hot-head">
        <span class="h-hot-title">🔥 热点活动</span>
        <span class="h-hot-more" @click="activeTab='all'; fetchActivities()">更多 ›</span>
      </div>
      <div class="h-hot-scroll">
        <div v-if="hotActivities.length === 0" class="h-hot-empty">暂无热点活动</div>
        <div v-else v-for="act in hotActivities" :key="act.id" class="h-hot-card" @click="$router.push('/activity/'+act.id)">
          <div class="h-hot-name">{{ act.title }}</div>
          <div class="h-hot-meta">
            <span>📅 {{ formatDate(act.start_time) }}</span>
            <span>👥 {{ act.current_participants||0 }}人</span>
          </div>
          <div class="h-hot-tag">{{ act.city || act.location_name || '待定' }}</div>
        </div>
      </div>
    </div>

    <!-- ═══ Content ═══ -->
    <div class="h-content">
      <div v-if="loading" class="h-loading"><div class="h-spinner"></div></div>

      <div v-else-if="activities.length===0" class="h-empty">
        <div class="h-empty-icon">🏕️</div>
        <p>暂无活动，来发起一个吧！</p>
        <router-link to="/create" class="h-empty-btn">+ 发起活动</router-link>
      </div>

      <div v-else>
        <div v-for="act in activities" :key="act.id" class="h-card" @click="$router.push('/activity/'+act.id)">
          <div class="h-card-title">{{ act.title }}</div>
          <div class="h-card-meta">
            <span>📅 {{ formatDate(act.start_time) }}</span>
            <span>📍 {{ act.city || act.location_name || '待定' }}</span>
            <span>👥 {{ act.current_participants||0 }}/{{ act.max_participants||'不限' }} 人</span>
          </div>
          <div class="h-card-foot">
            <span class="h-card-status" :style="{ color: act.status_color, background: (act.status_color||'#999')+'18' }">{{ act.status_text }}</span>
            <div class="h-card-info">
              <span v-if="act.distance_text">{{ act.distance_text }}</span>
              <span v-if="act.captain">👨‍💼 {{ act.captain.nickname }}</span>
            </div>
          </div>
        </div>

        <div v-if="hasMore" class="h-more">
          <button class="h-more-btn" @click="loadMore" :disabled="loadingMore">{{ loadingMore ? '加载中...' : '加载更多' }}</button>
        </div>
      </div>
    </div>

    <div style="height:80px"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { activitiesAPI } from '@/api'

const activeTab = ref('all')
const showFilters = ref(false)
const loading = ref(false), loadingMore = ref(false)
const activities = ref([]), hotActivities = ref([]), categories = ref([]), availableTags = ref([])
const page = ref(1), hasMore = ref(false)
const filters = ref({ date: '', tags: [], category: '' })

async function fetchActivities(reset = true) {
  if (reset) page.value = 1
  loading.value = true
  try {
    const params = { page: page.value, per_page: 20 }
    if (filters.value.category) params.category = filters.value.category
    if (filters.value.date) params.date = filters.value.date
    if (filters.value.tags.length) params.tags = filters.value.tags.join(',')
    const res = await activitiesAPI.list(params)
    if (res.data.code === 0) {
      const data = res.data.data
      activities.value = reset ? data.activities : [...activities.value, ...data.activities]
      hasMore.value = data.activities.length === 20
    }
  } catch (e) {} finally { loading.value = false }
}

async function fetchNearby() {
  loading.value = true
  try {
    let lat, lon
    if (navigator.geolocation) {
      try { const pos = await new Promise((resolve, reject) => { navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 }) }); lat = pos.coords.latitude; lon = pos.coords.longitude } catch (e) {}
    }
    const res = await activitiesAPI.nearby({ lat, lon })
    if (res.data.code === 0) activities.value = res.data.data.activities
  } catch (e) {} finally { loading.value = false }
}

function filterByCategory(name) { filters.value.category = name; fetchActivities() }
function toggleTag(tag) { const i = filters.value.tags.indexOf(tag); if (i>=0) filters.value.tags.splice(i,1); else filters.value.tags.push(tag); fetchActivities() }
async function loadMore() { loadingMore.value = true; page.value++; await fetchActivities(false); loadingMore.value = false }
function formatDate(d) { if(!d) return ''; const dt = new Date(d); return (dt.getMonth()+1)+'月'+dt.getDate()+'日 '+String(dt.getHours()).padStart(2,'0')+':'+String(dt.getMinutes()).padStart(2,'0') }

onMounted(async () => {
  fetchActivities()
  // Fetch hot activities sorted by participants
  try {
    const res = await activitiesAPI.list({ page: 1, per_page: 20 })
    if (res.data.code === 0) {
      hotActivities.value = (res.data.data.activities || [])
        .filter(a => a.current_participants > 0)
        .sort((a, b) => (b.current_participants || 0) - (a.current_participants || 0))
        .slice(0, 6)
    }
  } catch (e) {}
  try {
    const [cr, tr] = await Promise.all([activitiesAPI.categories(), activitiesAPI.tags()])
    if (cr.data.code === 0) categories.value = cr.data.data
    if (tr.data.code === 0) availableTags.value = tr.data.data
  } catch (e) {}
})
</script>

<style scoped>
.home-page { background: #F2F4F5; min-height: 100vh; font-family: 'PingFang SC', sans-serif }

/* Header */
.h-header { background: linear-gradient(180deg, #06D6A0 0%, #0096C7 100%); padding: 48px 0 28px }
.h-header-row { display: flex; align-items: center; padding: 0 16px }
.h-title { flex: 1; color: #fff; font-size: 18px; font-weight: 700 }
.h-filter-btn { background: rgba(255,255,255,.25); border: 1px solid rgba(255,255,255,.4); color: #fff; padding: 6px 14px; border-radius: 16px; font-size: 14px; cursor: pointer }

/* Tabs */
.h-tabs-wrap { background: #fff; border-bottom: 1px solid #f0f0f0 }
.h-tabs { display: flex; gap: 8px; padding: 10px 16px; overflow-x: auto; -webkit-overflow-scrolling: touch }
.h-tabs button { padding: 7px 16px; border-radius: 18px; font-size: 14px; font-weight: 500; white-space: nowrap; background: #F2F4F5; color: #666; border: none; cursor: pointer }
.h-tabs button.on { background: #06D6A0; color: #fff; font-weight: 600 }

/* Filters */
.h-filters { background: #fff; padding: 14px 18px; border-bottom: 1px solid #f0f0f0 }
.h-frow { margin-bottom: 12px }
.h-frow:last-child { margin-bottom: 0 }
.h-flabel { font-size: 14px; font-weight: 600; color: #666; margin-bottom: 6px; display: block }
.h-finput { width: 100%; padding: 10px 12px; border: 1px solid #E0E0E0; border-radius: 8px; font-size: 14px; box-sizing: border-box; color: #333 }
.h-ftags { display: flex; flex-wrap: wrap; gap: 8px }
.h-ftag { background: #F2F4F5; padding: 6px 14px; border-radius: 14px; font-size: 13px; cursor: pointer; color: #666 }
.h-ftag.on { background: #06D6A0; color: #fff }

/* ═══ Hotspot ═══ */
.h-hotspot { background: linear-gradient(135deg, #E8F8F5, #D4F2E8); margin: 12px 16px; border-radius: 16px; padding: 14px 0; border: 1.5px solid #06D6A0 }
.h-hot-head { display: flex; justify-content: space-between; align-items: center; padding: 0 16px; margin-bottom: 10px }
.h-hot-title { font-size: 15px; font-weight: 700; color: #06D6A0 }
.h-hot-more { font-size: 13px; color: #0096C7; cursor: pointer }
.h-hot-scroll { display: flex; gap: 10px; overflow-x: auto; padding: 0 16px; -webkit-overflow-scrolling: touch }
.h-hot-empty { font-size: 13px; color: #999; padding: 8px 0 }
.h-hot-card { min-width: 140px; max-width: 160px; background: #fff; border-radius: 10px; padding: 12px; flex-shrink: 0; cursor: pointer; box-shadow: 0 2px 6px rgba(0,0,0,.06) }
.h-hot-card:active { opacity: .85 }
.h-hot-name { font-size: 14px; font-weight: 600; color: #333; margin-bottom: 6px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden }
.h-hot-meta { font-size: 11px; color: #999; display: flex; gap: 8px; margin-bottom: 6px }
.h-hot-tag { display: inline-block; padding: 2px 8px; background: #06D6A0; color: #fff; border-radius: 8px; font-size: 11px }

/* Content */
.h-content { padding: 0 0 12px }

/* Loading */
.h-loading { text-align: center; padding: 40px 0 }
.h-spinner { width: 32px; height: 32px; border: 3px solid #E8F8F5; border-top-color: #06D6A0; border-radius: 50%; margin: 0 auto; animation: spin .8s linear infinite }
@keyframes spin { to { transform: rotate(360deg) } }

/* Empty */
.h-empty { text-align: center; padding: 80px 20px; color: #999 }
.h-empty-icon { font-size: 48px; margin-bottom: 12px }
.h-empty p { font-size: 15px; margin-bottom: 16px }
.h-empty-btn { display: inline-flex; padding: 10px 24px; background: #06D6A0; color: #fff; border-radius: 24px; font-size: 15px; font-weight: 600; text-decoration: none }

/* Cards */
.h-card { background: #fff; margin: 8px 16px; border-radius: 14px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,.04); cursor: pointer }
.h-card:active { background: #f9f9f9 }
.h-card-title { font-size: 16px; font-weight: 700; color: #333; margin-bottom: 8px; line-height: 1.4 }
.h-card-meta { display: flex; gap: 10px; flex-wrap: wrap; font-size: 13px; color: #999; margin-bottom: 8px }
.h-card-foot { display: flex; justify-content: space-between; align-items: center }
.h-card-status { padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: 600 }
.h-card-info { display: flex; gap: 10px; font-size: 12px; color: #999 }

/* More */
.h-more { text-align: center; padding: 20px }
.h-more-btn { padding: 10px 32px; background: #fff; border: 1px solid #06D6A0; color: #06D6A0; border-radius: 20px; font-size: 14px; cursor: pointer }
.h-more-btn:disabled { opacity: .5 }
</style>
