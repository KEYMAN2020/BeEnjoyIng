<template>
  <div class="ca-page">
    <!-- ═══ Teal Header ═══ -->
    <div class="ca-header">
      <div class="ca-header-row">
        <span class="ca-back" @click="$router.back()">← 取消</span>
        <span class="ca-title">发起活动</span>
        <span style="width:50px"></span>
      </div>
    </div>

    <!-- ═══ Form ═══ -->
    <form class="ca-form" @submit.prevent="handleSubmit">
      <div class="ca-group">
        <label class="ca-label">活动标题 *</label>
        <input v-model="form.title" class="ca-input" placeholder="给活动取个名字吧" maxlength="50" required />
      </div>

      <div class="ca-group">
        <label class="ca-label">活动分类</label>
        <select v-model="form.category_id" class="ca-select">
          <option value="">请选择分类</option>
          <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
        </select>
      </div>

      <div class="ca-row">
        <div class="ca-group" style="flex:1">
          <label class="ca-label">开始时间 *</label>
          <input v-model="form.start_time" type="datetime-local" class="ca-input" required />
        </div>
        <div class="ca-group" style="flex:1">
          <label class="ca-label">结束时间</label>
          <input v-model="form.end_time" type="datetime-local" class="ca-input" />
        </div>
      </div>

      <div class="ca-group" style="position:relative">
        <label class="ca-label">活动地点</label>
        <input v-model="form.location_name" class="ca-input" placeholder="输入地址后选择建议" autocomplete="off"
          @input="onAddressInput" @focus="onAddressFocus" @blur="onAddressBlur" />
        <ul v-if="addressSuggestions.length > 0" class="ca-suggestions">
          <li v-for="(item, idx) in addressSuggestions" :key="idx" @mousedown.prevent="selectAddress(item)" class="ca-sug-item">
            <span class="ca-sug-name">{{ item.name }}</span>
            <span class="ca-sug-dist">{{ item.district || item.address }}</span>
          </li>
        </ul>
      </div>

      <div class="ca-group">
        <label class="ca-label">城市</label>
        <input v-model="form.city" class="ca-input" placeholder="如：北京、上海" />
      </div>

      <div class="ca-row">
        <div class="ca-group" style="flex:1">
          <label class="ca-label">最大人数</label>
          <input v-model.number="form.max_participants" type="number" class="ca-input" placeholder="不限" min="2" />
        </div>
        <div class="ca-group" style="flex:1">
          <label class="ca-label">费用 (¥)</label>
          <input v-model.number="form.price" type="number" class="ca-input" placeholder="0 免费" min="0" step="0.01" />
        </div>
      </div>

      <div class="ca-group">
        <label class="ca-label">活动详情</label>
        <textarea v-model="form.description" class="ca-textarea" rows="5" placeholder="介绍你的活动吧..." maxlength="2000"></textarea>
      </div>

      <div class="ca-group">
        <label class="ca-label">标签</label>
        <div class="ca-tags-wrap">
          <span v-for="tag in form.tags" :key="tag" class="ca-tag" @click="removeTag(tag)">{{ tag }} ✕</span>
          <input v-model="tagInput" class="ca-tag-input" @keyup.enter.prevent="addTag" placeholder="输入标签后按回车添加" />
        </div>
      </div>

      <p v-if="error" class="ca-error">{{ error }}</p>

      <button type="submit" class="ca-submit" :disabled="submitting">
        {{ submitting ? '创建中...' : '发起活动' }}
      </button>
    </form>

    <div style="height:80px"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { activitiesAPI } from '@/api'

const router = useRouter()
const form = ref({ title:'', category_id:'', start_time:'', end_time:'', location_name:'', location_address:'', location_lng:null, location_lat:null, city:'', max_participants:null, price:0, description:'', tags:[] })
const tagInput = ref('')
const error = ref('')
const submitting = ref(false)
const categories = ref([])
const addressSuggestions = ref([])
let addressTimer = null

async function onAddressInput(e) {
  const val = e.target?.value?.trim() || ''
  if (addressTimer) clearTimeout(addressTimer)
  if (val.length < 1) { addressSuggestions.value = []; return }
  addressTimer = setTimeout(async () => {
    try {
      const res = await fetch('/api/v1/geo/search?keyword=' + encodeURIComponent(val) + '&city=' + encodeURIComponent(form.value.city || ''))
      const data = await res.json()
      addressSuggestions.value = data.code === 0 ? (data.data || []).slice(0,6) : []
    } catch(e) { addressSuggestions.value = [] }
  }, 300)
}

function onAddressFocus() { if (form.value.location_name?.trim()) { const e = { target: { value: form.value.location_name } }; onAddressInput(e) } }
function onAddressBlur() { setTimeout(() => { addressSuggestions.value = [] }, 200) }

function selectAddress(item) {
  form.value.location_name = item.name
  form.value.location_address = item.address || item.name
  form.value.city = form.value.city || item.district || ''
  if (item.location) { const parts = item.location.split(','); form.value.location_lng = parseFloat(parts[0]); form.value.location_lat = parseFloat(parts[1]) }
  addressSuggestions.value = []
}

function addTag() { const t = tagInput.value.trim(); if (t && !form.value.tags.includes(t)) { form.value.tags.push(t); tagInput.value = '' } }
function removeTag(tag) { form.value.tags = form.value.tags.filter(t => t !== tag) }

async function handleSubmit() {
  error.value = ''
  if (!form.value.title || !form.value.start_time) { error.value = '请填写活动标题和开始时间'; return }
  submitting.value = true
  try {
    const res = await activitiesAPI.create(form.value)
    if (res.data.code === 0) router.push(`/activity/${res.data.data.id}`)
    else error.value = res.data.message || '创建失败'
  } catch (e) { error.value = e.response?.data?.message || '网络错误' }
  finally { submitting.value = false }
}

onMounted(async () => {
  try { const res = await activitiesAPI.categories(); if (res.data.code === 0) categories.value = res.data.data.categories } catch (e) {}
})
</script>

<style scoped>
.ca-page { background: #F2F4F5; min-height: 100vh; font-family: 'PingFang SC', sans-serif }

/* Header */
.ca-header { background: linear-gradient(180deg, #06D6A0 0%, #0096C7 100%); padding: 48px 0 28px }
.ca-header-row { display: flex; align-items: center; padding: 0 16px }
.ca-back { color: #fff; font-size: 16px; cursor: pointer; font-weight: 500 }
.ca-title { flex: 1; text-align: center; color: #fff; font-size: 17px; font-weight: 600 }

/* Form */
.ca-form { padding: 16px }
.ca-group { margin-bottom: 16px }
.ca-label { display: block; font-size: 14px; font-weight: 600; color: #555; margin-bottom: 6px }
.ca-row { display: flex; gap: 12px }

/* Inputs */
.ca-input { width: 100%; padding: 12px 14px; border: 1px solid #E0E0E0; border-radius: 10px; font-size: 15px; color: #333; background: #fff; outline: none; box-sizing: border-box }
.ca-input:focus { border-color: #06D6A0 }
.ca-input::placeholder { color: #B0B0B0 }
.ca-select { width: 100%; padding: 12px 14px; border: 1px solid #E0E0E0; border-radius: 10px; font-size: 15px; background: #fff; outline: none; color: #333; box-sizing: border-box }
.ca-select:focus { border-color: #06D6A0 }
.ca-textarea { width: 100%; padding: 12px 14px; border: 1px solid #E0E0E0; border-radius: 10px; font-size: 15px; color: #333; background: #fff; outline: none; resize: vertical; min-height: 100px; box-sizing: border-box }
.ca-textarea:focus { border-color: #06D6A0 }

/* Suggestions */
.ca-suggestions { position: absolute; left: 0; right: 0; top: 100%; background: #fff; border: 1px solid #E0E0E0; border-radius: 10px; box-shadow: 0 4px 16px rgba(0,0,0,.1); z-index: 100; list-style: none; margin: 4px 0 0; padding: 4px 0; max-height: 220px; overflow-y: auto }
.ca-sug-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; cursor: pointer; font-size: 14px }
.ca-sug-item:hover { background: #E8F8F5 }
.ca-sug-name { color: #333; font-weight: 500 }
.ca-sug-dist { color: #999; font-size: 12px; margin-left: 8px; white-space: nowrap }

/* Tags */
.ca-tags-wrap { display: flex; flex-wrap: wrap; gap: 6px; border: 1px solid #E0E0E0; border-radius: 10px; padding: 8px; background: #fff }
.ca-tag { background: #06D6A0; color: #fff; padding: 4px 12px; border-radius: 12px; font-size: 13px; cursor: pointer }
.ca-tag-input { flex: 1; min-width: 120px; border: none; padding: 8px; font-size: 15px; outline: none; background: transparent }

/* Error / Submit */
.ca-error { color: #FF6B6B; font-size: 14px; text-align: center; margin-bottom: 8px }
.ca-submit { width: 100%; padding: 14px; background: linear-gradient(135deg, #06D6A0, #0096C7); color: #fff; border: none; border-radius: 12px; font-size: 17px; font-weight: 700; cursor: pointer }
.ca-submit:active { opacity: .85 }
.ca-submit:disabled { opacity: .6; cursor: not-allowed }
</style>
