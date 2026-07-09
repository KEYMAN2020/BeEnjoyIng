<template>
  <div class="edit-page-v3">
    <div class="pf-back">
      <button @click="$router.back()">← 返回</button>
    </div>

    <div v-if="loading" class="empty-state">加载中...</div>
    <div v-else class="edit-form-v3">
      <h3>编辑资料</h3>
      <div class="edit-avatar-row" @click="triggerUpload">
        <div class="edit-avatar-preview">
          <img v-if="avatarPreview" :src="avatarPreview" />
          <span v-else>{{ (form.nickname || "?")[0] }}</span>
        </div>
        <div class="edit-avatar-hint">点击更换头像</div>
        <input type="file" ref="fileInput" accept="image/*" style="display:none" @change="handleFile" />
      </div>

      <div class="edit-field">
        <label>昵称</label>
        <input v-model="form.nickname" placeholder="请输入昵称" />
      </div>

      <div class="edit-field">
        <label>性别</label>
        <select v-model="form.gender">
          <option value="male">男</option>
          <option value="female">女</option>
          <option value="other">保密</option>
        </select>
      </div>

      <div class="edit-field">
        <label>出生年份</label>
        <input v-model.number="form.birth_year" type="number" placeholder="如 1965" />
      </div>

      <div class="edit-field">
        <label>城市</label>
        <input v-model="form.city" placeholder="如 北京" />
      </div>

      <div class="edit-field">
        <label>兴趣（逗号分隔）</label>
        <input v-model="form.interests" placeholder="如 摄影,旅游,书法" />
      </div>

      <div class="edit-field">
        <label>简介</label>
        <textarea v-model="form.bio" placeholder="介绍一下自己..."></textarea>
      </div>

      <!-- Privacy Settings -->
      <div class="edit-field">
        <label>隐身模式</label>
        <select v-model="form.ghost_mode">
          <option :value="1">开启</option>
          <option :value="0">关闭</option>
        </select>
      </div>

      <div class="edit-field">
        <label>允许私信</label>
        <select v-model="form.allow_private_msg">
          <option :value="1">允许</option>
          <option :value="0">不允许</option>
        </select>
      </div>

      <div class="edit-field">
        <label>允许查看资料</label>
        <select v-model="form.allow_profile_view">
          <option :value="1">允许</option>
          <option :value="0">不允许</option>
        </select>
      </div>

      <div class="edit-btns">
        <button class="btn-cancel" @click="$router.back()">取消</button>
        <button class="btn-save" @click="saveProfile" :disabled="saving">{{ saving ? '保存中...' : '保存' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api, { usersAPI } from '@/api'

const router = useRouter()
const loading = ref(true)
const saving = ref(false)
const fileInput = ref(null)
const avatarPreview = ref(null)

function triggerUpload() {
  fileInput.value?.click()
}

async function handleFile(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const fd = new FormData()
  fd.append("file", file)
  fd.append("subdir", "avatars")
  try {
    const res = await api.post("/upload", fd, { headers: { "Content-Type": "multipart/form-data" } })
    if (res.data.code === 0) {
      avatarPreview.value = res.data.data.url
    }
  } catch (e) { alert("上传失败") }
}

const form = reactive({
  nickname: '',
  gender: 'male',
  birth_year: null,
  city: '',
  interests: '',
  bio: '',
  ghost_mode: 0,
  allow_private_msg: 0,
  allow_profile_view: 0
})

async function saveProfile() {
  if (!form.nickname.trim()) { alert('昵称不能为空'); return }
  saving.value = true
  try {
    const res = await usersAPI.updateMe({
      nickname: form.nickname.trim(),
      gender: form.gender,
      birth_year: form.birth_year || null,
      city: form.city.trim(),
      interests: form.interests.trim(),
      bio: form.bio.trim(),
      ghost_mode: form.ghost_mode === 1,
      allow_private_msg: form.allow_private_msg === 1,
      allow_profile_view: form.allow_profile_view === 1,
      ...(avatarPreview.value ? { avatar_url: avatarPreview.value } : {})
    })
    if (res.data.code === 0) {
      alert('保存成功')
      router.back()
    } else {
      alert(res.data.message || '保存失败')
    }
  } catch (e) { alert('网络错误') }
  saving.value = false
}

onMounted(async () => {
  try {
    const res = await usersAPI.me()
    if (res.data.code === 0) {
      const data = res.data.data.user || res.data.data || {}
      const p = data.profile || {}
      form.nickname = data.nickname || ''
      avatarPreview.value = data.avatar_url || null
      form.gender = p.gender || 'male'
      form.birth_year = p.birth_year || null
      form.city = p.city || ''
      form.interests = p.interests || ''
      form.bio = p.bio || ''
      form.ghost_mode = p.ghost_mode ? 1 : 0
      form.allow_private_msg = p.allow_private_msg ? 1 : 0
      form.allow_profile_view = p.allow_profile_view ? 1 : 0
    }
  } catch (e) {}
  loading.value = false
})
</script>

<style scoped>
.edit-page-v3 { background: #f5f5f5; min-height: 100vh; padding-bottom: 80px; }
.pf-back { display: flex; align-items: center; padding: 12px 16px; background: #fff; border-bottom: 1px solid #f0f0f0; }
.pf-back button { background: none; border: none; color: #FF6B35; font-size: 15px; font-weight: 600; cursor: pointer; padding: 0; }
.edit-form-v3 { background: #fff; border-radius: 16px; padding: 24px; margin: 16px auto; max-width: 400px; box-shadow: 0 1px 4px rgba(0,0,0,.04); }
.edit-form-v3 h3 { text-align: center; margin: 0 0 20px; font-size: 18px; }
.edit-field { margin-bottom: 14px; }
.edit-field label { display: block; font-size: 13px; color: #666; margin-bottom: 4px; }
.edit-field input, .edit-field select, .edit-field textarea { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 10px; font-size: 14px; box-sizing: border-box; }
.edit-field textarea { height: 80px; resize: vertical; }
.edit-btns { display: flex; gap: 12px; margin-top: 20px; }
.edit-btns button { flex: 1; padding: 12px; border: none; border-radius: 10px; font-size: 14px; cursor: pointer; }
.btn-save { background: #FF6B35; color: #fff; font-weight: 600; }
.btn-save:disabled { opacity: 0.6; }
.btn-cancel { background: #f5f5f5; color: #666; }
.edit-avatar-row { display: flex; flex-direction: column; align-items: center; padding: 16px 0; cursor: pointer; }
.edit-avatar-preview { width: 72px; height: 72px; border-radius: 50%; background: linear-gradient(135deg, #FF6B35, #FFB74D); color: #fff; font-size: 32px; font-weight: 700; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.edit-avatar-preview img { width: 100%; height: 100%; object-fit: cover; }
.edit-avatar-hint { font-size: 12px; color: #999; margin-top: 6px; }
.edit-avatar-row .edit-avatar-preview { border: 3px solid #FF6B35; }

.empty-state { text-align: center; color: #999; padding: 60px 20px; font-size: 14px; }
</style>
