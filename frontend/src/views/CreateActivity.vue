<template>
  <div class="create-page">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">‹ 取消</button>
      <h1 style="flex:1;text-align:center">发起活动</h1>
      <div style="width:50px"></div>
    </div>

    <form class="create-form" @submit.prevent="handleSubmit">
      <div class="form-group">
        <label>活动标题 *</label>
        <input v-model="form.title" placeholder="给活动取个名字吧" maxlength="50" required />
      </div>

      <div class="form-group">
        <label>活动分类</label>
        <select v-model="form.category_id">
          <option value="">请选择分类</option>
          <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
        </select>
      </div>

      <div class="form-group">
        <label>开始时间 *</label>
        <input v-model="form.start_time" type="datetime-local" required />
      </div>

      <div class="form-group">
        <label>结束时间</label>
        <input v-model="form.end_time" type="datetime-local" />
      </div>

      <div class="form-group">
        <label>活动地点</label>
        <input v-model="form.location_name" placeholder="请输入地点" />
      </div>

      <div class="form-group">
        <label>城市</label>
        <input v-model="form.city" placeholder="如：北京、上海" />
      </div>

      <div class="form-group">
        <label>最大人数</label>
        <input v-model.number="form.max_participants" type="number" placeholder="不填则不限制" min="2" />
      </div>

      <div class="form-group">
        <label>费用 (¥)</label>
        <input v-model.number="form.price" type="number" placeholder="0 表示免费" min="0" step="0.01" />
      </div>

      <div class="form-group">
        <label>活动详情</label>
        <textarea v-model="form.description" rows="5" placeholder="介绍你的活动吧..." maxlength="2000"></textarea>
      </div>

      <div class="form-group">
        <label>标签</label>
        <div class="tag-input">
          <span v-for="tag in form.tags" :key="tag" class="tag" @click="removeTag(tag)">
            {{ tag }} ✕
          </span>
          <input v-model="tagInput" @keyup.enter.prevent="addTag" placeholder="输入标签后按回车添加" style="flex:1;min-width:120px;border:none;padding:8px" />
        </div>
      </div>

      <p v-if="error" class="form-error">{{ error }}</p>

      <button class="btn btn-primary btn-block" :disabled="submitting">
        {{ submitting ? '创建中...' : '发起活动' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { activitiesAPI } from '@/api'

const router = useRouter()

const form = ref({
  title: '',
  category_id: '',
  start_time: '',
  end_time: '',
  location_name: '',
  city: '',
  max_participants: null,
  price: 0,
  description: '',
  tags: []
})
const tagInput = ref('')
const error = ref('')
const submitting = ref(false)
const categories = ref([])

function addTag() {
  const t = tagInput.value.trim()
  if (t && !form.value.tags.includes(t)) {
    form.value.tags.push(t)
    tagInput.value = ''
  }
}

function removeTag(tag) {
  form.value.tags = form.value.tags.filter(t => t !== tag)
}

async function handleSubmit() {
  error.value = ''
  if (!form.value.title || !form.value.start_time) {
    error.value = '请填写活动标题和开始时间'
    return
  }
  submitting.value = true
  try {
    const res = await activitiesAPI.create(form.value)
    if (res.data.code === 0) {
      router.push(`/activity/${res.data.data.id}`)
    } else {
      error.value = res.data.message || '创建失败'
    }
  } catch (e) {
    error.value = e.response?.data?.message || '网络错误'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    const res = await activitiesAPI.categories()
    if (res.data.code === 0) categories.value = res.data.data.categories
  } catch (e) {}
})
</script>

<style scoped>
.create-form {
  padding: 16px;
}
select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 15px;
  background: #fff;
  outline: none;
}
select:focus {
  border-color: var(--primary);
}
textarea {
  resize: vertical;
  min-height: 100px;
}
.tag-input {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 6px;
}
.tag-input .tag {
  background: var(--primary-light);
  color: #fff;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
}
.back-btn {
  background: none;
  font-size: 16px;
  color: var(--primary);
  font-weight: 500;
}
</style>
