<template>
  <div class="edit-page">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">‹ 取消</button>
      <h1 style="flex:1;text-align:center">编辑活动</h1>
      <div style="width:50px"></div>
    </div>

    <div v-if="loading" class="loading-spinner"><div class="spinner"></div></div>

    <form v-else class="edit-form" @submit.prevent="handleSubmit">
      <div class="form-group">
        <label>活动标题</label>
        <input v-model="form.title" required />
      </div>
      <div class="form-group">
        <label>开始时间</label>
        <input v-model="form.start_time" type="datetime-local" required />
      </div>
      <div class="form-group">
        <label>结束时间</label>
        <input v-model="form.end_time" type="datetime-local" />
      </div>
      <div class="form-group">
        <label>活动地点</label>
        <input v-model="form.location_name" />
      </div>
      <div class="form-group">
        <label>最大人数</label>
        <input v-model.number="form.max_participants" type="number" min="2" />
      </div>
      <div class="form-group">
        <label>费用 (¥)</label>
        <input v-model.number="form.fee" type="number" min="0" step="0.01" />
      </div>
      <div class="form-group">
        <label>活动详情</label>
        <textarea v-model="form.description" rows="5" maxlength="2000"></textarea>
      </div>
      <p v-if="error" class="form-error">{{ error }}</p>
      <button class="btn btn-primary btn-block" :disabled="submitting">
        {{ submitting ? '保存中...' : '保存修改' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { activitiesAPI } from '@/api'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const form = ref({
  title: '',
  start_time: '',
  end_time: '',
  location_name: '',
  max_participants: null,
  fee: 0,
  description: ''
})
const error = ref('')
const submitting = ref(false)

function formatDateForInput(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const offset = d.getTimezoneOffset()
  const local = new Date(d.getTime() - offset * 60000)
  return local.toISOString().slice(0, 16)
}

onMounted(async () => {
  try {
    const res = await activitiesAPI.detail(route.params.id)
    if (res.data.code === 0) {
      const act = res.data.data
      form.value = {
        title: act.title,
        start_time: formatDateForInput(act.start_time),
        end_time: formatDateForInput(act.end_time),
        location_name: act.location_name || '',
        max_participants: act.max_participants,
        fee: act.fee || 0,
        description: act.description || ''
      }
    }
  } catch (e) {} finally { loading.value = false }
})

async function handleSubmit() {
  error.value = ''
  submitting.value = true
  try {
    const res = await activitiesAPI.update(route.params.id, form.value)
    if (res.data.code === 0) {
      router.push(`/activity/${route.params.id}`)
    } else {
      error.value = res.data.message || '更新失败'
    }
  } catch (e) {
    error.value = '网络错误'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.edit-form { padding: 16px; }
textarea { resize: vertical; min-height: 80px; }
.back-btn { background: none; font-size: 16px; color: var(--primary); font-weight: 500; }
</style>
