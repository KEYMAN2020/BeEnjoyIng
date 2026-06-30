<template>
  <div class="mine-page-v3">
    <!-- Header -->
    <div class="mine-header-v3">
      <div class="mine-avatar-wrap" @click="goProfile">
        <div class="mine-avatar-v3">
          <img v-if="user?.avatar_url" :src="user.avatar_url" @error="onAvatarError" />
          <span v-else>{{ (user?.nickname || '?')[0] }}</span>
        </div>
        <div class="mine-edit-btn-v3">✐</div>
      </div>
      <div class="mine-nickname-v3">{{ user?.nickname || '加载中...' }}</div>
      <div class="mine-level-v3">新芽 · 活力值 {{ user?.vitality_score || 0 }}</div>
    </div>

    <!-- Progress -->
    <div class="mine-progress-v3">
      <div class="mp-row">
        <span class="mp-label">升级进度</span>
        <span class="mp-value">{{ user?.vitality_score || 0 }}/200</span>
      </div>
      <div class="mp-bar"><div class="mp-fill" :style="{ width: Math.min((user?.vitality_score || 0) / 200 * 100, 100) + '%' }"></div></div>
      <div class="mp-flowers">🌸 花朵积分：<span>{{ user?.flower_score || 0 }}</span></div>
    </div>

    <!-- Sub page: Activities -->
    <template v-if="subPage === 'activities'">
      <div class="sub-back-v3">
        <button @click="goBack()">← 返回</button>
        <span>我的活动</span>
      </div>
      <div class="sub-card-v3">
        <div v-if="loadingSub" class="empty-state">加载中...</div>
        <div v-else-if="myActivities.length === 0" class="empty-state">暂无活动</div>
        <div v-else>
          <div v-for="act in myActivities" :key="act.id" class="act-item-v3" @click="$router.push('/activity/' + act.id)">
            <div class="act-title-v3">{{ act.title }}</div>
            <div class="act-meta-v3">📅 {{ (act.start_time || '').slice(0, 10) }} | 📍 {{ act.city }} | 👥 {{ act.current_participants }}/{{ act.max_participants }}</div>
            
            <div v-if="act.status_text" style="font-size:11px;margin-top:4px" :style="{color: act.status_text === '已结束' ? '#999' : '#52C41A'}">{{ act.status_text }}</div>
            <span class="act-tag-v3" :class="act.is_captain || act.is_creator ? 'tag-created-v3' : 'tag-joined-v3'">{{ act.is_captain || act.is_creator ? '我创建的' : '我报名的' }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- Sub page: Favorites -->
    <template v-else-if="subPage === 'favorites'">
      <div class="sub-back-v3">
        <button @click="goBack()">← 返回</button>
        <span>我的收藏</span>
      </div>
      <div class="sub-card-v3">
        <div v-if="loadingSub" class="empty-state">加载中...</div>
        <div v-else-if="myFavorites.length === 0" class="empty-state">暂无收藏</div>
        <div v-else>
          <div v-for="act in myFavorites" :key="act.id" class="act-item-v3" @click="$router.push('/activity/' + act.id)">
            <div class="act-title-v3">{{ act.title }}</div>
            <div class="act-meta-v3">📅 {{ (act.start_time || '').slice(0, 10) }} | 📍 {{ act.city }} | 👥 {{ act.current_participants }}/{{ act.max_participants }}</div>
          </div>
        </div>
      </div>
    </template>

    <!-- Main Menu -->
    <template v-else>
      <!-- 活动 -->
      <div class="section-wrap-v3">
        <div class="section-title-v3">活动</div>
        <div class="section-item-v3" @click="openSub('activities')"><span class="si-icon">📋</span><span class="si-text">我的活动</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3" @click="openSub('favorites')"><span class="si-icon">⭐</span><span class="si-text">我的收藏</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3" @click="$router.push('/contacts')"><span class="si-icon">👥</span><span class="si-text">我的好友</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3"><span class="si-icon">🏆</span><span class="si-text">活力成就</span><span class="si-extra">达成 3 项</span><span class="si-arrow">›</span></div>
      </div>

      <!-- 安全 -->
      <div class="section-wrap-v3">
        <div class="section-title-v3">安全</div>
        <div class="section-item-v3"><span class="si-icon">🆘</span><span class="si-text">紧急联系人</span><span class="si-extra">未设置</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3"><span class="si-icon">💚</span><span class="si-text">健康声明</span><span class="si-extra">未填写</span><span class="si-arrow">›</span></div>
      </div>

      <!-- 设置 -->
      <div class="section-wrap-v3">
        <div class="section-title-v3">设置</div>
        <div class="section-item-v3"><span class="si-icon">🔤</span><span class="si-text">字体大小</span><span class="si-extra">标准</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3"><span class="si-icon">🔔</span><span class="si-text">消息通知</span><span class="si-extra">已开启</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3" @click="showChangePwd = true"><span class="si-icon">🔑</span><span class="si-text">修改密码</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3" @click="goProfile"><span class="si-icon">👤</span><span class="si-text">个人信息</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3"><span class="si-icon">🔒</span><span class="si-text">隐私设置</span><span class="si-arrow">›</span></div>
      </div>

      <button class="logout-btn-v3" @click="logout">退出登录</button>
    </template>

    <!-- Password Change Modal -->
    <div v-if="showChangePwd" class="modal-overlay" @click.self="showChangePwd = false">
      <div class="modal-card">
        <h3>修改密码</h3>
        <input v-model="pwdForm.old" type="password" placeholder="旧密码" class="modal-input" />
        <input v-model="pwdForm.newPwd" type="password" placeholder="新密码" class="modal-input" />
        <input v-model="pwdForm.confirm" type="password" placeholder="确认新密码" class="modal-input" />
        <div v-if="pwdError" class="modal-error">{{ pwdError }}</div>
        <div class="modal-btns">
          <button class="modal-cancel" @click="showChangePwd = false; pwdError = ''">取消</button>
          <button class="modal-submit" @click="changePassword" :disabled="changingPwd">{{ changingPwd ? '提交中...' : '确认' }}</button>
        </div>
      </div>
    </div>

    <div style="height:80px"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usersAPI, activitiesAPI, authAPI } from '@/api'

const router = useRouter()
const user = ref(null)
const subPage = ref('')
const myActivities = ref([])
const myFavorites = ref([])
const loadingSub = ref(false)
function goBack() { subPage.value = ''; router.replace({ query: {} }) }
const showChangePwd = ref(false)
const changingPwd = ref(false)
const pwdError = ref('')
const pwdForm = ref({ old: '', newPwd: '', confirm: '' })

let currentUserId = null

function goProfile() {
  router.push('/profile/' + currentUserId)
}

function onAvatarError(e) {
  e.target.style.display = 'none'
}

async function openSub(page) {
  subPage.value = page
  router.replace({ query: { tab: page } })
  loadingSub.value = true
  try {
    if (page === 'activities') {
      const res = await activitiesAPI.my({ type: 'all' })
      if (res.data.code === 0) myActivities.value = res.data.data.activities || res.data.data || []
    } else if (page === 'favorites') {
      const res = await activitiesAPI.myFavorites()
      if (res.data.code === 0) myFavorites.value = res.data.data.activities || res.data.data || []
    }
  } catch (e) {}
  loadingSub.value = false
}

async function changePassword() {
  const { old, newPwd, confirm } = pwdForm.value
  if (!old) { pwdError.value = '请输入旧密码'; return }
  if (!newPwd) { pwdError.value = '请输入新密码'; return }
  if (newPwd !== confirm) { pwdError.value = '两次密码不一致'; return }
  if (newPwd.length < 6) { pwdError.value = '密码至少6位'; return }
  pwdError.value = ''
  changingPwd.value = true
  try {
    const res = await authAPI.changePassword({ old_password: old, new_password: newPwd })
    if (res.data.code === 0) {
      alert('密码修改成功')
      showChangePwd.value = false
      pwdForm.value = { old: '', newPwd: '', confirm: '' }
    } else {
      pwdError.value = res.data.message || '修改失败'
    }
  } catch (e) { pwdError.value = '网络错误' }
  changingPwd.value = false
}

function logout() {
  if (!confirm('确定退出登录？')) return
  localStorage.removeItem('token')
  location.href = '/login'
}

onMounted(async () => {
  const tab = router.currentRoute.value.query.tab
  if (tab) await openSub(tab)
  try {
    const token = localStorage.getItem('token')
    if (token) {
      try { currentUserId = JSON.parse(atob(token.split('.')[1])).user_id } catch (e) {}
    }
    const res = await usersAPI.me()
    if (res.data.code === 0) { user.value = res.data.data.user || res.data.data || {}; if (user.value.user_id) currentUserId = user.value.user_id }
  } catch (e) {}
})
</script>

<style scoped>
.mine-page-v3 { background: #f5f5f5; min-height: 100vh; padding-bottom: 80px; }

/* Header */
.mine-header-v3 { background: linear-gradient(135deg, #FF6B35, #FF8A50); padding: 30px 20px 40px; text-align: center; border-radius: 0 0 24px 24px; }
.mine-avatar-wrap { width: 72px; height: 72px; margin: 0 auto 12px; position: relative; cursor: pointer; }
.mine-avatar-v3 { width: 72px; height: 72px; border-radius: 50%; background: #fff; color: #FF6B35; font-size: 32px; font-weight: 700; display: flex; align-items: center; justify-content: center; border: 3px solid rgba(255,255,255,.5); overflow: hidden; margin: 0 auto; }
.mine-avatar-v3 img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }
.mine-edit-btn-v3 { position: absolute; bottom: 0; right: -4px; width: 26px; height: 26px; border-radius: 50%; background: #fff; border: 2px solid #FF6B35; color: #FF6B35; font-size: 12px; display: flex; align-items: center; justify-content: center; }
.mine-nickname-v3 { color: #fff; font-size: 20px; font-weight: 700; margin: 8px 0 4px; }
.mine-level-v3 { display: inline-block; background: rgba(255,255,255,.25); color: #fff; padding: 2px 12px; border-radius: 10px; font-size: 12px; }

/* Progress */
.mine-progress-v3 { margin: 0 20px; background: #fff; border-radius: 14px; padding: 16px; box-shadow: 0 2px 12px rgba(0,0,0,.08); transform: translateY(-20px); }
.mp-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.mp-label { font-size: 13px; color: #666; }
.mp-value { font-size: 13px; color: #FF6B35; font-weight: 600; }
.mp-bar { height: 6px; background: #f0f0f0; border-radius: 3px; overflow: hidden; }
.mp-fill { height: 100%; background: linear-gradient(90deg, #FF6B35, #FF8A50); border-radius: 3px; transition: width .3s; }
.mp-flowers { display: flex; align-items: center; justify-content: flex-end; margin-top: 6px; font-size: 12px; color: #999; }
.mp-flowers span { color: #FF6B35; font-weight: 600; margin: 0 2px; }

/* Sections */
.section-wrap-v3 { margin: 8px 16px; }
.section-title-v3 { font-size: 12px; color: #999; padding: 8px 4px 4px; font-weight: 500; }
.section-item-v3 { display: flex; align-items: center; padding: 13px 16px; background: #fff; cursor: pointer; border-bottom: 1px solid #f5f5f5; font-size: 14px; color: #2D2D2D; }
.section-item-v3:first-child { border-radius: 14px 14px 0 0; }
.section-item-v3:last-child { border-radius: 0 0 14px 14px; border-bottom: none; }
.section-item-v3:only-child { border-radius: 14px; }
.si-icon { width: 28px; text-align: center; margin-right: 12px; font-size: 18px; }
.si-text { flex: 1; }
.si-extra { color: #999; font-size: 12px; margin-right: 8px; }
.si-arrow { color: #ccc; font-size: 14px; }

/* Logout */
.logout-btn-v3 { display: block; margin: 24px auto; background: none; border: 1px solid #ff4d4f; color: #ff4d4f; padding: 10px 0; width: calc(100% - 32px); border-radius: 14px; font-size: 15px; cursor: pointer; text-align: center; background: #fff; }

/* Sub pages */
.sub-back-v3 { display: flex; align-items: center; padding: 12px 16px; background: #fff; border-bottom: 1px solid #f0f0f0; position: sticky; top: 0; z-index: 10; }
.sub-back-v3 button { background: none; border: none; color: #FF6B35; font-size: 15px; font-weight: 600; cursor: pointer; padding: 0; }
.sub-back-v3 span { font-size: 16px; font-weight: 700; color: #2D2D2D; margin-left: 8px; }
.sub-card-v3 { margin: 12px 16px; background: #fff; border-radius: 14px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,.04); }
.act-item-v3 { padding: 14px 0; border-bottom: 1px solid #f5f5f5; cursor: pointer; }
.act-item-v3:last-child { border-bottom: none; }
.act-title-v3 { font-size: 15px; font-weight: 600; color: #2D2D2D; margin-bottom: 6px; }
.act-meta-v3 { font-size: 12px; color: #999; }
.act-tag-v3 { display: inline-block; padding: 2px 8px; border-radius: 8px; font-size: 11px; font-weight: 600; margin-top: 6px; }
.tag-created-v3 { background: #FFF3E0; color: #FF6B35; }
.tag-joined-v3 { background: #E8F5E9; color: #43A047; }
.empty-state { text-align: center; color: #999; padding: 60px 20px; font-size: 14px; }

/* Modal */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,.5); z-index: 9999; display: flex; align-items: center; justify-content: center; }
.modal-card { background: #fff; border-radius: 16px; padding: 24px; width: 85%; max-width: 360px; }
.modal-card h3 { text-align: center; margin: 0 0 20px; font-size: 18px; }
.modal-input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 10px; margin-bottom: 12px; font-size: 14px; box-sizing: border-box; }
.modal-error { color: #ff4d4f; font-size: 13px; margin-bottom: 12px; text-align: center; }
.modal-btns { display: flex; gap: 12px; }
.modal-cancel { flex: 1; padding: 12px; background: #f5f5f5; border: none; border-radius: 10px; font-size: 14px; cursor: pointer; }
.modal-submit { flex: 1; padding: 12px; background: #FF6B35; color: #fff; border: none; border-radius: 10px; font-size: 14px; cursor: pointer; font-weight: 600; }
.modal-submit:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
