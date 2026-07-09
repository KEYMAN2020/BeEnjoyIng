<template>
  <div class="mine-page-v3">
    <!-- ═══ Continuous Teal Header ═══ -->
    <div class="m-header">
      <div class="m-statebar">9:41</div>
      <div class="m-avatar-wrap" @click="goProfile">
        <div class="m-avatar">
          <img v-if="user?.avatar_url" :src="user.avatar_url" @error="onAvatarError" />
          <svg v-else width="30" height="30" viewBox="0 0 30 30"><circle fill="#06D6A0" cx="15" cy="10" r="5"/><path fill="#06D6A0" d="M5 25v-2a4 4 0 014-4h12a4 4 0 014 4v2z"/></svg>
        </div>
      </div>
      <div class="m-nickname">{{ user?.nickname || '加载中...' }}</div>
      <div class="m-bio">热爱生活，喜欢运动</div>
      
      <!-- Stats -->
      <div class="m-stats">
        <div class="m-stat"><div class="m-stat-num">{{ user?.stats?.activity_count || 0 }}</div><div class="m-stat-label">活动</div></div>
        <div class="m-stat"><div class="m-stat-num">{{ user?.stats?.friend_count || 0 }}</div><div class="m-stat-label">好友</div></div>
        <div class="m-stat"><div class="m-stat-num">{{ user?.vitality_score || 0 }}</div><div class="m-stat-label">活力值</div></div>
      </div>
    </div>

    <!-- Sub: Activities -->
    <template v-if="subPage === 'activities'">
      <div class="sub-back-v3"><button @click="closeSub">← 返回</button><span>我的活动</span></div>
      <div class="sub-card-v3">
        <div v-if="loadingSub" class="empty-state">加载中...</div>
        <div v-else-if="myActivities.length === 0" class="empty-state">暂无活动</div>
        <div v-else>
          <div v-for="act in myActivities" :key="act.id" class="act-item-v3" @click="goActivity(act.id)">
            <div class="act-title-v3">{{ act.title }}</div>
            <div class="act-meta-v3">{{ (act.start_time || '').slice(0, 10) }} | {{ act.city || act.location_name }}</div>
            <span class="act-tag-v3" :class="act.is_captain ? 'tag-created-v3' : 'tag-joined-v3'">{{ act.is_captain ? '我创建的' : '我报名的' }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- Sub: Favorites -->
    <template v-else-if="subPage === 'favorites'">
      <div class="sub-back-v3"><button @click="closeSub">← 返回</button><span>我的收藏</span></div>
      <div class="sub-card-v3">
        <div v-if="loadingSub" class="empty-state">加载中...</div>
        <div v-else-if="myFavorites.length === 0" class="empty-state">暂无收藏</div>
        <div v-else>
          <div v-for="fav in myFavorites" :key="fav.id" class="act-item-v3" @click="goActivity(fav.id)">
            <div class="act-title-v3">{{ fav.title }}</div>
            <div class="act-meta-v3">{{ (fav.start_time || '').slice(0, 10) }}</div>
          </div>
        </div>
      </div>
    </template>

    <!-- Sub: Achievements -->
    <template v-else-if="subPage === 'achievements'">
      <div class="sub-back-v3"><button @click="closeSub">← 返回</button><span>活力成就</span></div>
      <div class="sub-card-v3">
        <div v-for="ach in achievements" :key="ach.key" class="ach-item" :class="{ 'ach-done': ach.done }">
          <span class="ach-icon">{{ ach.done ? '✅' : '⬜' }}</span>
          <div class="ach-info"><div class="ach-name">{{ ach.name }}</div><div class="ach-desc">{{ ach.desc }}</div></div>
          <div class="ach-progress">{{ ach.current }}/{{ ach.target }}</div>
        </div>
      </div>
    </template>

    <!-- Sub: Privacy -->
    <template v-else-if="subPage === 'privacy'">
      <div class="sub-back-v3"><button @click="closeSub">← 返回</button><span>隐私设置</span></div>
      <div class="sub-card-v3">
        <div class="toggle-row" @click="privacy.allow_profile_view = !privacy.allow_profile_view"><span>允许他人查看我的资料</span><span class="toggle-sw" :class="{ on: privacy.allow_profile_view }"></span></div>
        <div class="toggle-row" @click="privacy.allow_private_msg = !privacy.allow_private_msg"><span>允许陌生人私信</span><span class="toggle-sw" :class="{ on: privacy.allow_private_msg }"></span></div>
        <div class="toggle-row" @click="privacy.ghost_mode = !privacy.ghost_mode"><span>隐身模式</span><span class="toggle-sw" :class="{ on: privacy.ghost_mode }"></span></div>
        <button class="btn-save" @click="savePrivacy">保存</button>
      </div>
    </template>

    <!-- Sub: Health -->
    <template v-else-if="subPage === 'health'">
      <div class="sub-back-v3"><button @click="closeSub">← 返回</button><span>健康声明</span></div>
      <div class="sub-card-v3">
        <select v-model="health.chronic"><option value="">慢性病史</option><option value="none">无</option><option value="hypertension">高血压</option><option value="diabetes">糖尿病</option><option value="heart">心脏病</option></select>
        <select v-model="health.allergy" style="margin-top:12px"><option value="">药物过敏</option><option value="none">无</option><option value="penicillin">青霉素</option><option value="sulfa">磺胺类</option></select>
        <input v-model="health.note" placeholder="备注" class="form-input" style="margin-top:12px" />
        <button class="btn-save" :disabled="savingHealth" @click="saveHealth" style="margin-top:16px">{{ savingHealth ? '保存中...' : '保存' }}</button>
      </div>
    </template>

    <!-- Sub: Emergency -->
    <template v-else-if="subPage === 'emergency'">
      <div class="sub-back-v3"><button @click="closeSub">← 返回</button><span>紧急联系人</span></div>
      <div class="sub-card-v3">
        <div v-if="emergencyContacts.length === 0" class="empty-state">暂无紧急联系人</div>
        <div v-for="(ec, i) in emergencyContacts" :key="i" class="ec-card">
          <div><b>{{ ec.name }}</b><br/><span style="color:#06D6A0">{{ ec.phone }}</span><br/><span style="color:#999;font-size:12px">{{ ec.relation }}</span></div>
          <button class="ec-del" @click="removeEmergencyContact(i)">删除</button>
        </div>
        <button class="btn-save" @click="showEmergencyForm = true">+ 添加</button>
      </div>
      <div v-if="showEmergencyForm" class="modal-overlay" @click.self="showEmergencyForm = false">
        <div class="modal-card">
          <h3>添加紧急联系人</h3>
          <input v-model="ecForm.name" placeholder="姓名" class="modal-input" />
          <input v-model="ecForm.phone" placeholder="手机号" class="modal-input" />
          <select v-model="ecForm.relation" class="modal-input"><option value="">关系</option><option>配偶</option><option>子女</option><option>父母</option><option>朋友</option></select>
          <div class="modal-btns"><button class="modal-cancel" @click="showEmergencyForm = false">取消</button><button class="modal-submit" @click="addEmergencyContact">确认</button></div>
        </div>
      </div>
    </template>

    <!-- Main Menu -->
    <template v-else>
      <div class="m-grid">
        <div class="m-gitem" @click="openSub('activities')"><div class="m-gicon" style="background:#E8F8F5;color:#06D6A0"><svg width="24" height="24" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="17" rx="2" fill="currentColor"/><rect x="3" y="8.5" width="18" height="1" fill="#fff"/><path d="M8.5 2V6h-1V2h1Zm8 0v4h-1V2h1Z" fill="currentColor"/></svg></div><div class="m-glabel">我的活动</div></div>
        <div class="m-gitem" @click="openSub('favorites')"><div class="m-gicon" style="background:#FFF8E1;color:#FFB800"><svg width="24" height="24" viewBox="0 0 24 24"><path d="M17 3H7a2 2 0 00-2 2v16l7-3 7 3V5a2 2 0 00-2-2z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></div><div class="m-glabel">我的收藏</div></div>
        <div class="m-gitem" @click="$router.push('/contacts')"><div class="m-gicon" style="background:#FFEBEE;color:#FF6B6B"><svg width="24" height="24" viewBox="0 0 24 24"><circle cx="9" cy="7" r="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M1 21v-2a4 4 0 014-4h8a4 4 0 014 4v2" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="18" cy="7" r="3" fill="none" stroke="currentColor" stroke-width="2"/><line x1="18" y1="12" x2="18" y2="16" stroke="currentColor" stroke-width="2"/><line x1="16" y1="14" x2="20" y2="14" stroke="currentColor" stroke-width="2"/></svg></div><div class="m-glabel">我的好友</div></div>
        <div class="m-gitem" @click="showAchievements"><div class="m-gicon" style="background:#FFF8E1;color:#FFB800"><svg width="24" height="24" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 22 12 18.27 5.82 22 7 14.14 2 9.27l6.91-1.01L12 2z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg></div><div class="m-glabel">活力成就</div></div>
        <div class="m-gitem" @click="showEmergency"><div class="m-gicon" style="background:#FFEBEE;color:#FF6B6B"><svg width="24" height="24" viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6A19.79 19.79 0 012.12 4.18 2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.362 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.338 1.85.573 2.81.7A2 2 0 0122 16.92z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></div><div class="m-glabel">紧急联系人</div></div>
        <div class="m-gitem" @click="showHealth"><div class="m-gicon" style="background:#E8F8F5;color:#06D6A0"><svg width="24" height="24" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" fill="none" stroke="currentColor" stroke-width="2"/><polyline points="14 2 14 8 20 8" fill="none" stroke="currentColor" stroke-width="2"/><line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2"/><line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2"/><polyline points="10 9 9 9 8 9" stroke="currentColor" stroke-width="2"/></svg></div><div class="m-glabel">健康声明</div></div>
        <div class="m-gitem" @click="toggleFontSize"><div class="m-gicon" style="background:#E3F2FD;color:#0096C7"><svg width="24" height="24" viewBox="0 0 24 24"><text x="4" y="18" font-size="14" font-weight="bold" fill="currentColor" font-family="sans-serif">A</text><text x="14" y="20" font-size="20" font-weight="bold" fill="currentColor" font-family="sans-serif">A</text></svg></div><div class="m-glabel">字体大小</div></div>
        <div class="m-gitem" @click="toggleNotify"><div class="m-gicon" style="background:#E3F2FD;color:#0096C7"><svg width="24" height="24" viewBox="0 0 24 24"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M13.73 21a2 2 0 01-3.46 0" fill="none" stroke="currentColor" stroke-width="2"/></svg></div><div class="m-glabel">消息通知</div></div>
        <div class="m-gitem" @click="showChangePwd = true"><div class="m-gicon" style="background:#E3F2FD;color:#0096C7"><svg width="24" height="24" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M7 11V7a5 5 0 0110 0v4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="16" r="1" fill="currentColor"/></svg></div><div class="m-glabel">修改密码</div></div>
        <div class="m-gitem" @click="goProfile"><div class="m-gicon" style="background:#E3F2FD;color:#0096C7"><svg width="24" height="24" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="7" r="4" fill="none" stroke="currentColor" stroke-width="2"/></svg></div><div class="m-glabel">个人信息</div></div>
        <div class="m-gitem" @click="showPrivacy"><div class="m-gicon" style="background:#E3F2FD;color:#0096C7"><svg width="24" height="24" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="none" stroke="currentColor" stroke-width="2"/></svg></div><div class="m-glabel">隐私设置</div></div>
        <div class="m-gitem" @click="logout"><div class="m-gicon" style="background:#FFEBEE;color:#FF6B6B"><svg width="24" height="24" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" fill="none" stroke="currentColor" stroke-width="2"/><polyline points="16 17 21 12 16 7" fill="none" stroke="currentColor" stroke-width="2"/><line x1="21" y1="12" x2="9" y2="12" stroke="currentColor" stroke-width="2"/></svg></div><div class="m-glabel" style="color:#FF6B6B">退出登录</div></div>
      </div>
    </template>

    <!-- Password Modal -->
    <div v-if="showChangePwd" class="modal-overlay" @click.self="showChangePwd = false">
      <div class="modal-card">
        <h3>修改密码</h3>
        <input v-model="pwdForm.old" type="password" placeholder="旧密码" class="modal-input" />
        <input v-model="pwdForm.newPwd" type="password" placeholder="新密码" class="modal-input" />
        <input v-model="pwdForm.confirm" type="password" placeholder="确认新密码" class="modal-input" />
        <div v-if="pwdError" class="modal-error">{{ pwdError }}</div>
        <div class="modal-btns"><button class="modal-cancel" @click="showChangePwd = false">取消</button><button class="modal-submit" @click="changePassword">确认</button></div>
      </div>
    </div>
    <div style="height:80px"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usersAPI, activitiesAPI, authAPI } from '@/api'

const router = useRouter()
const route = useRoute()
const user = ref(null)
const subPage = ref('')
const myActivities = ref([])
const myFavorites = ref([])
const loadingSub = ref(false)
const showChangePwd = ref(false)
const changingPwd = ref(false)
const pwdError = ref('')
const pwdForm = ref({ old: '', newPwd: '', confirm: '' })
let currentUserId = 4

// Wrapper functions for subpage navigation
function showAchievements() { openSub('achievements') }
function showEmergency() { openSub('emergency') }
function showHealth() { openSub('health') }
function showPrivacy() { openSub('privacy') }

const fontSizeLabels = { small: '小号', normal: '标准', large: '大号' }
const fontSize = ref(localStorage.getItem('fontSize') || 'normal')
function toggleFontSize() {
  const s = ['small','normal','large']; fontSize.value = s[(s.indexOf(fontSize.value)+1)%3]
  localStorage.setItem('fontSize', fontSize.value)
  document.documentElement.style.fontSize = {small:'15px',normal:'17px',large:'20px'}[fontSize.value]
}

const notifyEnabled = ref(localStorage.getItem('notifyEnabled') !== 'false')
function toggleNotify() { notifyEnabled.value = !notifyEnabled.value; localStorage.setItem('notifyEnabled', notifyEnabled.value) }

const achievements = ref([
  { key:'first_join', name:'初出茅庐', desc:'报名第1个活动', current:0, target:1, done:false },
  { key:'five_joins', name:'活跃分子', desc:'报名5个活动', current:0, target:5, done:false },
  { key:'ten_joins', name:'社交达人', desc:'报名10个活动', current:0, target:10, done:false },
  { key:'week_warrior', name:'周游达人', desc:'一周内参加3场', current:0, target:3, done:false },
  { key:'first_rate', name:'好评初体验', desc:'完成首次评价', current:0, target:1, done:false },
  { key:'create_first', name:'发起者', desc:'创建第1个活动', current:0, target:1, done:false },
])

const privacy = reactive({ allow_profile_view: true, allow_private_msg: true, ghost_mode: false })
async function savePrivacy() {
  try { await usersAPI.updateProfile(privacy); alert('已保存'); closeSub() }
  catch(e) { alert('保存失败') }
}

const emergencyContacts = ref(JSON.parse(localStorage.getItem('emergencyContacts') || '[]'))
const showEmergencyForm = ref(false), ecForm = ref({ name: '', phone: '', relation: '' })
function addEmergencyContact() {
  if (!ecForm.value.name || !ecForm.value.phone) { alert('请填写姓名和电话'); return }
  emergencyContacts.value.push({ ...ecForm.value })
  localStorage.setItem('emergencyContacts', JSON.stringify(emergencyContacts.value))
  ecForm.value = { name:'', phone:'', relation:'' }; showEmergencyForm.value = false
}
function removeEmergencyContact(i) {
  if (!confirm('确定删除？')) return
  emergencyContacts.value.splice(i,1)
  localStorage.setItem('emergencyContacts', JSON.stringify(emergencyContacts.value))
}

const health = ref(JSON.parse(localStorage.getItem('healthDeclaration') || '{"chronic":"","allergy":"","note":"","id":null}'))
const savingHealth = ref(false)
async function saveHealth() {
  savingHealth.value = true; health.value.id = Date.now()
  localStorage.setItem('healthDeclaration', JSON.stringify(health.value))
  alert('已保存'); savingHealth.value = false; closeSub()
}

function goProfile() {
  if (subPage.value) {
    subPage.value = ''
    router.replace({ query: {} }).then(() => { router.push('/profile/' + currentUserId) })
  } else {
    router.push('/profile/' + currentUserId)
  }
}
function goActivity(id) { router.push('/activity/' + id) }
function onAvatarError(e) { e.target.style.display = 'none' }

function closeSub() {
  subPage.value = ''
  router.replace({ query: {} })
}

watch(() => route.query.sub, (newSub) => {
  if (newSub && newSub !== subPage.value) openSub(newSub)
  else if (!newSub && subPage.value) subPage.value = ''
})

async function openSub(page) {
  subPage.value = page
  router.replace({ query: { ...route.query, sub: page } })
  loadingSub.value = true
  try {
    if (page === 'activities') {
      const res = await activitiesAPI.my({ type: 'all' }); const d = res.data || res
      if (d.code === 0) myActivities.value = d.data?.activities || d.data?.items || d.data || []
    } else if (page === 'favorites') {
      const res = await activitiesAPI.myFavorites(); const d = res.data || res
      if (d.code === 0) myFavorites.value = d.data?.activities || d.data?.favorites || d.data || []
    } else if (page === 'achievements') {
      try {
        const res = await usersAPI.achievements()
        const d = res.data || res
        if (d.code === 0 && d.data?.achievements) {
          const list = d.data.achievements
          achievements.value.forEach(a => {
            const m = list.find(x => x.key === a.key)
            if (m) { a.current = m.current; a.done = m.done }
          })
        }
      } catch(e) {}
    } else if (page === 'privacy') {
      try { const res = await usersAPI.me(); const p = (res.data||res)?.data?.user?.profile || (res.data||res)?.data?.profile || {}
        privacy.allow_profile_view = p.allow_profile_view !== false
        privacy.allow_private_msg = p.allow_private_msg !== false
        privacy.ghost_mode = p.ghost_mode === true }
      catch(e) {}
    }
  } catch(e) {}
  loadingSub.value = false
}

function changePassword() {
  const { old, newPwd, confirm } = pwdForm.value
  if (!old) { pwdError.value = '请输入旧密码'; return }
  if (!newPwd) { pwdError.value = '请输入新密码'; return }
  if (newPwd !== confirm) { pwdError.value = '两次不一致'; return }
  pwdError.value = ''; changingPwd.value = true
  authAPI.changePassword({ old_password: old, new_password: newPwd }).then(res => {
    const d = res.data || res
    if (d.code === 0) { alert('修改成功'); showChangePwd.value = false; pwdForm.value = { old:'', newPwd:'', confirm:'' } }
    else pwdError.value = d.message || '失败'
  }).catch(() => { pwdError.value = '网络错误' }).finally(() => { changingPwd.value = false })
}

function logout() { if (confirm('确定退出登录？')) { localStorage.clear(); location.href = '/app/login' } }

onMounted(async () => {
  document.documentElement.style.fontSize = {small:'15px',normal:'17px',large:'20px'}[fontSize.value]
  // Restore sub-page from URL query
  if (route.query.sub) {
    openSub(route.query.sub)
  }
  try {
    const token = localStorage.getItem('token')
    if (token) { try { currentUserId = JSON.parse(atob(token.split('.')[1])).user_id } catch(e) {} }
    const res = await usersAPI.me(); const d = res.data || res
    if (d.code === 0) user.value = d.data?.user || d.data || {}
  } catch(e) {}
})
</script>

<style scoped>
.mine-page-v3{background:#F2F4F5;min-height:100vh;padding-bottom:80px}

/* ═══ Header — continuous teal gradient ═══ */
.m-header{background:linear-gradient(180deg,#06D6A0 0%,#0096C7 100%);padding:16px 20px 28px;text-align:center;border-radius:0 0 24px 24px}
.m-statebar{color:#fff;font-size:15px;font-weight:600;margin-bottom:10px;text-align:left}
.m-avatar-wrap{width:64px;height:64px;margin:0 auto 12px;cursor:pointer}
.m-avatar{width:64px;height:64px;border-radius:50%;border:3px solid rgba(255,255,255,.5);display:flex;align-items:center;justify-content:center;overflow:hidden;margin:0 auto;background:rgba(255,255,255,.2)}
.m-avatar img{width:100%;height:100%;object-fit:cover}
.m-nickname{color:#fff;font-size:18px;font-weight:700;margin-bottom:4px}
.m-bio{color:rgba(255,255,255,.8);font-size:13px;margin-bottom:16px}
.m-stats{display:flex;justify-content:center;gap:32px}
.m-stat{text-align:center;color:#fff}
.m-stat-num{font-size:18px;font-weight:700}
.m-stat-label{font-size:12px;opacity:.8;margin-top:2px}

/* 4-column Grid */
.m-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; padding: 12px 16px }
.m-gitem { background: #fff; border-radius: 12px; padding: 14px 6px; text-align: center; cursor: pointer; box-shadow: 0 1px 4px rgba(0,0,0,.04); transition: transform .1s }
.m-gitem:active { transform: scale(.96) }
.m-gicon { width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px }
.m-glabel { font-size: 12px; color: #333; font-weight: 500; line-height: 1.3 }
.sub-back-v3{display:flex;align-items:center;padding:12px 16px;background:#fff;border-bottom:1px solid #f0f0f0;position:sticky;top:0;z-index:10}
.sub-back-v3 button{background:none;border:none;color:#06D6A0;font-size:15px;font-weight:600;cursor:pointer;padding:0}
.sub-back-v3 span{font-size:16px;font-weight:700;color:#2D2D2D;margin-left:8px}
.sub-card-v3{margin:12px 16px;background:#fff;border-radius:14px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.04)}
.act-item-v3{padding:14px 0;border-bottom:1px solid #f5f5f5;cursor:pointer}
.act-item-v3:last-child{border-bottom:none}
.act-title-v3{font-size:15px;font-weight:600;color:#2D2D2D;margin-bottom:6px}
.act-meta-v3{font-size:12px;color:#999}
.act-tag-v3{display:inline-block;padding:2px 8px;border-radius:8px;font-size:11px;font-weight:600;margin-top:6px}
.tag-created-v3{background:#FFF3E0;color:#06D6A0}.tag-joined-v3{background:#E8F5E9;color:#43A047}
.empty-state{text-align:center;color:#999;padding:60px 20px;font-size:14px}
.ach-item{display:flex;align-items:center;padding:14px 0;border-bottom:1px solid #f5f5f5}
.ach-item:last-child{border-bottom:none}.ach-item.ach-done{opacity:.6}
.ach-icon{font-size:24px;margin-right:12px}.ach-info{flex:1}
.ach-name{font-size:15px;font-weight:600}.ach-desc{font-size:12px;color:#999;margin-top:2px}
.ach-progress{font-size:12px;color:#06D6A0;font-weight:600}
.toggle-row{display:flex;align-items:center;justify-content:space-between;padding:14px 0;border-bottom:1px solid #f5f5f5;cursor:pointer}
.toggle-row:last-child{border-bottom:none}.toggle-row span:first-child{font-size:14px;color:#2D2D2D}
.toggle-sw{width:44px;height:26px;background:#ddd;border-radius:13px;position:relative;transition:background .2s}
.toggle-sw::after{content:'';position:absolute;width:22px;height:22px;background:#fff;border-radius:50%;top:2px;left:2px;transition:left .2s;box-shadow:0 1px 3px rgba(0,0,0,.2)}
.toggle-sw.on{background:#06D6A0}.toggle-sw.on::after{left:20px}
.btn-save{display:block;width:100%;margin-top:16px;padding:12px;background:#06D6A0;color:#fff;border:none;border-radius:14px;font-size:15px;font-weight:600;cursor:pointer}
.ec-card{display:flex;align-items:center;justify-content:space-between;padding:14px 0;border-bottom:1px solid #f5f5f5}
.ec-card:last-child{border-bottom:none}
.ec-del{background:none;border:1px solid #ff4d4f;color:#ff4d4f;padding:4px 12px;border-radius:8px;font-size:12px;cursor:pointer}
select{width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:10px;font-size:14px;background:#fff}
.form-input{width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:10px;font-size:14px;box-sizing:border-box}
.modal-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center}
.modal-card{background:#fff;border-radius:16px;padding:24px;width:85%;max-width:360px}
.modal-card h3{text-align:center;margin:0 0 20px;font-size:18px}
.modal-input{width:100%;padding:12px;border:1px solid #ddd;border-radius:10px;margin-bottom:12px;font-size:14px;box-sizing:border-box}
.modal-error{color:#ff4d4f;font-size:13px;margin-bottom:12px;text-align:center}
.modal-btns{display:flex;gap:12px}
.modal-cancel{flex:1;padding:12px;background:#f5f5f5;border:none;border-radius:10px;font-size:14px;cursor:pointer}
.modal-submit{flex:1;padding:12px;background:#06D6A0;color:#fff;border:none;border-radius:10px;font-size:14px;cursor:pointer;font-weight:600}
</style>
