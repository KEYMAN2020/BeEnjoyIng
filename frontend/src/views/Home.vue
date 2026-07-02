<template>
  <div class="home-page">
    <div class="page-header">
      <h1>🏕️ 发现活动</h1>
      <div style="flex:1"></div>
      <button class="btn btn-sm btn-outline" @click="showFilters = !showFilters">🔍 筛选</button>
    </div>

    <div class="quick-tabs">
      <button :class="{ active: activeTab === 'all' }" @click="activeTab = 'all'; fetchActivities()">全部</button>
      <button :class="{ active: activeTab === 'nearby' }" @click="activeTab = 'nearby'; fetchNearby()">📍 附近</button>
      <button v-for="cat in categories" :key="cat.id" :class="{ active: activeTab === cat.name }" @click="activeTab = cat.name; filterByCategory(cat.name)">{{ cat.name }}</button>
    </div>

    <div class="filters" v-if="showFilters">
      <div class="filter-row">
        <label>📅 日期</label>
        <input type="date" v-model="filters.date" @change="fetchActivities" />
      </div>
      <div class="filter-row">
        <label>🏷️ 标签</label>
        <div class="tag-list">
          <span v-for="tag in availableTags" :key="tag" class="tag" :class="{ active: filters.tags.includes(tag) }" @click="toggleTag(tag)">{{ tag }}</span>
        </div>
      </div>
    </div>

    <div class="container" style="padding-top:10px">
      <div v-if="loading" class="loading-spinner"><div class="spinner"></div></div>

      <div v-else-if="activities.length === 0" class="empty-state">
        <span class="icon">🏕️</span>
        <p>暂无活动，来发起一个吧！</p>
        <router-link to="/create" class="btn btn-primary" style="margin-top:16px;display:inline-flex">+ 发起活动</router-link>
      </div>

      <div v-else>
        <div v-for="act in activities" :key="act.id" class="activity-card" @click="$router.push(`/activity/${act.id}`)" style="position:relative">
          <button v-if="act.status_text === '已结束'" class="card-delete-btn" @click.stop="confirmDelete(act)" title="删除">🗑️</button>
          <div class="card-header">
            <div class="card-title">{{ act.title }}</div>
            <div class="card-meta">
              <span>📅 {{ formatDate(act.start_time) }}</span>
              <span>📍 {{ act.city || act.location_name || '待定' }}</span>
              <span>👥 {{ act.current_participants || 0 }}/{{ act.max_participants || '不限' }} 人</span>
            </div>
          </div>
          <div class="card-footer">
            <span class="status-tag" :style="{ color: act.status_color, background: act.status_color + '1a' }">{{ act.status_text }}</span>
            <div class="card-stats">
              <span v-if="act.distance_text">{{ act.distance_text }}</span>
              <span v-if="act.captain">👨‍💼 {{ act.captain.nickname }}</span>
            </div>
          </div>
        </div>
        <div v-if="hasMore" style="text-align:center;padding:24px">
          <button class="btn btn-outline" @click="loadMore" :disabled="loadingMore">{{ loadingMore ? '加载中...' : '加载更多' }}</button>
        </div>
      </div>
    </div>
    <div class="page-bottom-padding"></div>

    <!-- Delete Modal -->
    <div v-if="deleteModal.show" class="del-overlay">
      <div class="del-card">
        <div class="del-title">确认删除</div>
        <div class="del-msg">确定要删除此活动吗？</div>
        <div class="del-btns">
          <button class="del-cancel" @click="deleteModal.show = false">取消</button>
          <button class="del-ok" @click="doDelete">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { activitiesAPI } from "@/api"

const activeTab = ref("all")
const showFilters = ref(false)
const loading = ref(false)
const loadingMore = ref(false)
const activities = ref([])
const categories = ref([])
const availableTags = ref([])
const page = ref(1)
const hasMore = ref(false)
const showDeleteDialog = ref(false)
const deleting = ref(false)
const deletingAct = ref(null)

const deleteModal = ref({ show: false, act: null })

function confirmDelete(act) {
  deleteModal.value = { show: true, act }
}

async function doDelete() {
  const act = deleteModal.value.act
  if (!act) return
  activities.value = activities.value.filter(a => a.id !== act.id)
  deleteModal.value = { show: false, act: null }
}
const filters = ref({ date: "", tags: [], category: "" })

async function fetchActivities(reset = true) {
  if (reset) page.value = 1
  loading.value = true
  try {
    const params = { page: page.value, per_page: 20 }
    if (filters.value.category) params.category = filters.value.category
    if (filters.value.date) params.date = filters.value.date
    if (filters.value.tags.length) params.tags = filters.value.tags.join(",")
    const res = await activitiesAPI.list(params)
    if (res.data.code === 0) {
      const data = res.data.data
      activities.value = reset ? data.activities : [...activities.value, ...data.activities]
      hasMore.value = data.activities.length === 20
    }
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function fetchNearby() {
  loading.value = true
  try {
    let lat, lon
    if (navigator.geolocation) {
      try {
        const pos = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 })
        })
        lat = pos.coords.latitude; lon = pos.coords.longitude
      } catch (e) {}
    }
    const res = await activitiesAPI.nearby({ lat, lon })
    if (res.data.code === 0) activities.value = res.data.data.activities
  } catch (e) {}
  finally { loading.value = false }
}

function filterByCategory(name) { filters.value.category = name; fetchActivities() }
function toggleTag(tag) {
  const idx = filters.value.tags.indexOf(tag)
  if (idx >= 0) filters.value.tags.splice(idx, 1)
  else filters.value.tags.push(tag)
  fetchActivities()
}
async function loadMore() { loadingMore.value = true; page.value++; await fetchActivities(false); loadingMore.value = false }
function formatDate(d) {
  if (!d) return ""
  const dt = new Date(d)
  return (dt.getMonth()+1) + "月" + dt.getDate() + "日 " + String(dt.getHours()).padStart(2,"0") + ":" + String(dt.getMinutes()).padStart(2,"0")
}
onMounted(async () => {
  fetchActivities()
  try {
    const [catRes, tagRes] = await Promise.all([activitiesAPI.categories(), activitiesAPI.tags()])
    if (catRes.data.code === 0) categories.value = catRes.data.data
    if (tagRes.data.code === 0) availableTags.value = tagRes.data.data
  } catch (e) {}
})
</script>

<style scoped>
.quick-tabs { display: flex; gap: 8px; padding: 10px 16px; overflow-x: auto; -webkit-overflow-scrolling: touch; background: var(--bg-white); border-bottom: 1px solid var(--border); }
.quick-tabs button { padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 500; white-space: nowrap; background: var(--bg); color: var(--text-secondary); transition: all 0.2s; }
.quick-tabs button.active { background: var(--primary); color: #fff; font-weight: 600; }
.filters { background: var(--bg-white); padding: 14px 18px; border-bottom: 1px solid var(--border); }
.filter-row { margin-bottom: 12px; }
.filter-row label { font-size: 15px; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px; display: block; }
.tag-list { display: flex; flex-wrap: wrap; gap: 8px; }
.tag-list .tag { background: var(--bg); padding: 6px 14px; border-radius: 14px; font-size: 14px; cursor: pointer; transition: all 0.2s; }
.tag-list .tag.active { background: var(--primary-light); color: #fff; }
.del-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,.5); z-index: 99999; display: flex; align-items: center; justify-content: center; }
.del-card { background: #fff; border-radius: 16px; width: 300px; padding: 24px; box-shadow: 0 8px 32px rgba(0,0,0,.2); }
.del-title { text-align: center; font-size: 18px; font-weight: 700; color: #333; margin-bottom: 12px; }
.del-msg { text-align: center; color: #666; font-size: 14px; margin-bottom: 20px; }
.del-btns { display: flex; gap: 12px; }
.del-cancel { flex: 1; padding: 12px; background: #f5f5f5; border: none; border-radius: 10px; font-size: 14px; cursor: pointer; color: #666; }
.del-ok { flex: 1; padding: 12px; background: #ff4d4f; color: #fff; border: none; border-radius: 10px; font-size: 14px; cursor: pointer; font-weight: 600; }
</style>
