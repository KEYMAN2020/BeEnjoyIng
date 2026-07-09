<template>
  <div class="pe-page">
    <div class="pe-header">
      <span class="pe-back" @click="$router.back()">← 取消</span>
      <span class="pe-title">编辑资料</span>
      <span class="pe-save" @click="saveProfile" :class="{ disabled: saving }">{{ saving ? '保存中...' : '保存' }}</span>
    </div>

    <div v-if="loading" class="pe-loading">加载中...</div>

    <template v-else>
      <div class="pe-card">
        <div class="pe-row">
          <span class="pe-label">昵称</span>
          <input v-model="form.nickname" class="pe-input" placeholder="你的昵称" maxlength="20" />
        </div>
        <div class="pe-row">
          <span class="pe-label">真实姓名</span>
          <input v-model="form.real_name" class="pe-input" placeholder="真实姓名" maxlength="20" />
        </div>
        <div class="pe-row">
          <span class="pe-label">性别</span>
          <select v-model="form.gender" class="pe-select">
            <option value="">请选择</option>
            <option value="male">男</option>
            <option value="female">女</option>
            <option value="other">保密</option>
          </select>
        </div>
        <div class="pe-row">
          <span class="pe-label">出生年份</span>
          <input v-model="form.birth_year" class="pe-input" type="number" placeholder="如 1965" min="1940" max="2010" />
        </div>
        <div class="pe-row">
          <span class="pe-label">城市</span>
          <input v-model="form.city" class="pe-input" placeholder="所在城市" maxlength="30" />
        </div>
        <div class="pe-row">
          <span class="pe-label">区县</span>
          <input v-model="form.district" class="pe-input" placeholder="所在区县" maxlength="30" />
        </div>
        <div class="pe-row pe-row-col">
          <span class="pe-label">个人简介</span>
          <textarea v-model="form.bio" class="pe-textarea" placeholder="介绍一下自己..." maxlength="200" rows="3"></textarea>
        </div>
        <div class="pe-row pe-row-col">
          <span class="pe-label">兴趣爱好</span>
          <input v-model="form.interests" class="pe-input" placeholder="如：太极,广场舞,旅游（逗号分隔）" maxlength="100" />
        </div>
      </div>

      <div class="pe-card">
        <div class="pe-row">
          <span class="pe-label">隐身模式</span>
          <span class="pe-toggle" :class="{ on: form.ghost_mode }" @click="form.ghost_mode = !form.ghost_mode"></span>
        </div>
        <div class="pe-row">
          <span class="pe-label">允许私信</span>
          <span class="pe-toggle" :class="{ on: form.allow_private_msg }" @click="form.allow_private_msg = !form.allow_private_msg"></span>
        </div>
        <div class="pe-row">
          <span class="pe-label">允许查看资料</span>
          <span class="pe-toggle" :class="{ on: form.allow_profile_view }" @click="form.allow_profile_view = !form.allow_profile_view"></span>
        </div>
      </div>

      <div class="pe-actions">
        <button class="pe-btn-cancel" @click="$router.back()">取消</button>
        <button class="pe-btn-save" @click="saveProfile" :disabled="saving">{{ saving ? '保存中...' : '保存' }}</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usersAPI } from '@/api'

const router = useRouter()
const loading = ref(true)
const saving = ref(false)
const form = reactive({
  nickname: '',
  real_name: '',
  gender: '',
  birth_year: '',
  city: '',
  district: '',
  bio: '',
  interests: '',
  ghost_mode: false,
  allow_private_msg: true,
  allow_profile_view: true
})

async function loadProfile() {
  try {
    const res = await usersAPI.me()
    const d = res.data || res
    if (d.code === 0) {
      const u = d.data?.user || d.data || {}
      const p = u.profile || {}
      form.nickname = u.nickname || ''
      form.real_name = p.real_name || ''
      form.gender = p.gender || ''
      form.birth_year = p.birth_year || ''
      form.city = p.city || ''
      form.district = p.district || ''
      form.bio = p.bio || ''
      form.interests = p.interests || ''
      form.ghost_mode = !!p.ghost_mode
      form.allow_private_msg = p.allow_private_msg !== false
      form.allow_profile_view = p.allow_profile_view !== false
    }
  } catch (e) {
    alert('加载资料失败')
  }
  loading.value = false
}

async function saveProfile() {
  saving.value = true
  try {
    await usersAPI.updateProfile({
      nickname: form.nickname,
      real_name: form.real_name,
      gender: form.gender || null,
      birth_year: form.birth_year ? parseInt(form.birth_year) : null,
      city: form.city || null,
      district: form.district || null,
      bio: form.bio || null,
      interests: form.interests || null,
      ghost_mode: form.ghost_mode,
      allow_private_msg: form.allow_private_msg,
      allow_profile_view: form.allow_profile_view
    })
    alert('保存成功')
    router.back()
  } catch (e) {
    alert(e.response?.data?.message || '保存失败')
  }
  saving.value = false
}

onMounted(loadProfile)
</script>

<style scoped>
.pe-page { background: #F2F4F5; min-height: 100vh; font-family: 'PingFang SC', sans-serif }

.pe-header { display: flex; align-items: center; padding: 12px 16px; background: #fff; border-bottom: 1px solid #eee }
.pe-back { color: #0096C7; font-size: 14px; cursor: pointer }
.pe-title { flex: 1; text-align: center; font-size: 17px; font-weight: 600; color: #333 }
.pe-save { color: #06D6A0; font-size: 14px; font-weight: 600; cursor: pointer }
.pe-save.disabled { color: #ccc; pointer-events: none }

.pe-loading { text-align: center; padding: 60px; color: #999; font-size: 14px }

.pe-card { background: #fff; border-radius: 12px; margin: 12px 16px; padding: 4px 0; box-shadow: 0 1px 4px rgba(0,0,0,.04) }
.pe-row { display: flex; align-items: center; padding: 14px 16px; border-bottom: 1px solid #f5f5f5; font-size: 14px }
.pe-row:last-child { border-bottom: none }
.pe-row-col { flex-direction: column; align-items: flex-start }
.pe-row-col .pe-label { margin-bottom: 6px }
.pe-label { color: #666; flex-shrink: 0; width: 80px }
.pe-input, .pe-select { flex: 1; border: none; outline: none; font-size: 14px; color: #333; text-align: right; background: none }
.pe-select { cursor: pointer }
.pe-input::placeholder { color: #ccc }
.pe-textarea { width: 100%; border: 1px solid #eee; border-radius: 8px; padding: 10px; font-size: 14px; color: #333; outline: none; resize: none; box-sizing: border-box }
.pe-textarea::placeholder { color: #ccc }

.pe-toggle { width: 42px; height: 24px; background: #ddd; border-radius: 12px; position: relative; cursor: pointer; transition: .2s }
.pe-toggle::after { content: ''; position: absolute; width: 20px; height: 20px; background: #fff; border-radius: 50%; top: 2px; left: 2px; transition: .2s }
.pe-toggle.on { background: #06D6A0 }
.pe-toggle.on::after { left: 20px }

.pe-actions { display: flex; gap: 12px; padding: 20px 16px }
.pe-btn-cancel { flex: 1; padding: 14px; background: #fff; color: #666; border: 1px solid #ddd; border-radius: 12px; font-size: 16px; cursor: pointer }
.pe-btn-save { flex: 1; padding: 14px; background: #06D6A0; color: #fff; border: none; border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer }
.pe-btn-save:disabled { background: #ccc }
.pe-btn-save:active, .pe-btn-cancel:active { opacity: .8 }
</style>
