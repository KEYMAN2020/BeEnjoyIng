<template>
  <div class="mine-page-v3">
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
    <div class="mine-progress-v3">
      <div class="mp-row"><span class="mp-label">升级进度</span><span class="mp-value">{{ user?.vitality_score || 0 }}/200</span></div>
      <div class="mp-bar"><div class="mp-fill" :style="{ width: Math.min((user?.vitality_score || 0) / 200 * 100, 100) + '%' }"></div></div>
      <div class="mp-flowers">🌸 花朵积分：<span>{{ user?.flower_score || 0 }}</span></div>
    </div>

    <!-- Sub: Activities -->
    <template v-if="subPage === 'activities'">
      <div class="sub-back-v3"><button @click="subPage = ''">← 返回</button><span>我的活动</span></div>
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
      <div class="sub-back-v3"><button @click="subPage = ''">← 返回</button><span>我的收藏</span></div>
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
      <div class="sub-back-v3"><button @click="subPage = ''">← 返回</button><span>活力成就</span></div>
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
      <div class="sub-back-v3"><button @click="subPage = ''">← 返回</button><span>隐私设置</span></div>
      <div class="sub-card-v3">
        <div class="toggle-row" @click="privacy.allowProfileView = !privacy.allowProfileView"><span>允许他人查看我的资料</span><span class="toggle-sw" :class="{ on: privacy.allowProfileView }"></span></div>
        <div class="toggle-row" @click="privacy.allowPrivateMsg = !privacy.allowPrivateMsg"><span>允许陌生人私信</span><span class="toggle-sw" :class="{ on: privacy.allowPrivateMsg }"></span></div>
        <div class="toggle-row" @click="privacy.ghostMode = !privacy.ghostMode"><span>隐身模式</span><span class="toggle-sw" :class="{ on: privacy.ghostMode }"></span></div>
        <button class="btn-save" @click="savePrivacy">保存</button>
      </div>
    </template>

    <!-- Sub: Health -->
    <template v-else-if="subPage === 'health'">
      <div class="sub-back-v3"><button @click="subPage = ''">← 返回</button><span>健康声明</span></div>
      <div class="sub-card-v3">
        <select v-model="health.chronic"><option value="">慢性病史</option><option value="none">无</option><option value="hypertension">高血压</option><option value="diabetes">糖尿病</option><option value="heart">心脏病</option></select>
        <select v-model="health.allergy" style="margin-top:12px"><option value="">药物过敏</option><option value="none">无</option><option value="penicillin">青霉素</option><option value="sulfa">磺胺类</option></select>
        <input v-model="health.note" placeholder="备注" class="form-input" style="margin-top:12px" />
        <button class="btn-save" :disabled="savingHealth" @click="saveHealth" style="margin-top:16px">{{ savingHealth ? '保存中...' : '保存' }}</button>
      </div>
    </template>

    <!-- Sub: Emergency -->
    <template v-else-if="subPage === 'emergency'">
      <div class="sub-back-v3"><button @click="subPage = ''">← 返回</button><span>紧急联系人</span></div>
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
      <div class="section-wrap-v3"><div class="section-title-v3">活动</div>
        <div class="section-item-v3" @click="openSub('activities')"><span class="si-icon">📋</span><span class="si-text">我的活动</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3" @click="openSub('favorites')"><span class="si-icon">⭐</span><span class="si-text">我的收藏</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3" @click="$router.push('/contacts')"><span class="si-icon">👥</span><span class="si-text">我的好友</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3" @click="showAchievements"><span class="si-icon">🏆</span><span class="si-text">活力成就</span><span class="si-extra">达成 {{ achievements.filter(a=>a.done).length }} 项</span><span class="si-arrow">›</span></div>
      </div>
      <div class="section-wrap-v3"><div class="section-title-v3">安全</div>
        <div class="section-item-v3" @click="showEmergency"><span class="si-icon">🆘</span><span class="si-text">紧急联系人</span><span class="si-extra">{{ emergencyContacts.length ? '已设置 '+emergencyContacts.length+' 人' : '未设置' }}</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3" @click="showHealth"><span class="si-icon">💚</span><span class="si-text">健康声明</span><span class="si-extra">{{ health.id ? '已填写' : '未填写' }}</span><span class="si-arrow">›</span></div>
      </div>
      <div class="section-wrap-v3"><div class="section-title-v3">设置</div>
        <div class="section-item-v3" @click="toggleFontSize"><span class="si-icon">🔤</span><span class="si-text">字体大小</span><span class="si-extra">{{ fontSizeLabels[fontSize] }}</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3" @click="toggleNotify"><span class="si-icon">🔔</span><span class="si-text">消息通知</span><span class="si-extra">{{ notifyEnabled ? '已开启' : '已关闭' }}</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3" @click="showChangePwd = true"><span class="si-icon">🔑</span><span class="si-text">修改密码</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3" @click="goProfile"><span class="si-icon">👤</span><span class="si-text">个人信息</span><span class="si-arrow">›</span></div>
        <div class="section-item-v3" @click="showPrivacy"><span class="si-icon">🔒</span><span class="si-text">隐私设置</span><span class="si-arrow">›</span></div>
      </div>
      <button class="logout-btn-v3" @click="logout">退出登录</button>
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
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { usersAPI, activitiesAPI, authAPI } from '@/api'

const router = useRouter()
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
function showAchievements() { subPage.value = 'achievements' }
function showEmergency() { subPage.value = 'emergency' }
function showHealth() { subPage.value = 'health' }
function showPrivacy() { subPage.value = 'privacy' }

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

const privacy = reactive({ allowProfileView: true, allowPrivateMsg: true, ghostMode: false })
async function savePrivacy() {
  try { await usersAPI.updateProfile(privacy); alert('已保存'); subPage.value = '' }
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
  alert('已保存'); subPage.value = ''; savingHealth.value = false
}

function goProfile() { router.push('/profile/' + currentUserId) }
function goActivity(id) { router.push('/activity/' + id) }
function onAvatarError(e) { e.target.style.display = 'none' }

async function openSub(page) {
  subPage.value = page; loadingSub.value = true
  try {
    if (page === 'activities') {
      const res = await activitiesAPI.my({ type: 'all' }); const d = res.data || res
      if (d.code === 0) myActivities.value = d.data?.activities || d.data?.items || d.data || []
    } else if (page === 'favorites') {
      const res = await activitiesAPI.myFavorites(); const d = res.data || res
      if (d.code === 0) myFavorites.value = d.data?.activities || d.data?.favorites || d.data || []
    } else if (page === 'achievements') {
      try { const res = await usersAPI.me(); const u = (res.data||res)?.data?.user || (res.data||res)?.data || {}
        const c = u.stats?.activity_count || 0
        achievements.value.forEach((a,i) => { a.current = c; a.done = c >= a.target }) }
      catch(e) {}
    } else if (page === 'privacy') {
      try { const res = await usersAPI.me(); const p = (res.data||res)?.data?.user?.profile || (res.data||res)?.data?.profile || {}
        privacy.allowProfileView = p.allow_profile_view !== false
        privacy.allowPrivateMsg = p.allow_private_msg !== false
        privacy.ghostMode = p.ghost_mode === true }
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
  try {
    const token = localStorage.getItem('token')
    if (token) { try { currentUserId = JSON.parse(atob(token.split('.')[1])).user_id } catch(e) {} }
    const res = await usersAPI.me(); const d = res.data || res
    if (d.code === 0) user.value = d.data?.user || d.data || {}
  } catch(e) {}
})
</script>

<style scoped>
.mine-page-v3{background:#f5f5f5;min-height:100vh;padding-bottom:80px}
.mine-header-v3{background:linear-gradient(135deg,#06D6A0,#0096C7);padding:30px 20px 40px;text-align:center;border-radius:0 0 24px 24px}
.mine-avatar-wrap{width:72px;height:72px;margin:0 auto 12px;position:relative;cursor:pointer}
.mine-avatar-v3{width:72px;height:72px;border-radius:50%;background:#fff;color:#06D6A0;font-size:32px;font-weight:700;display:flex;align-items:center;justify-content:center;border:3px solid rgba(255,255,255,.5);overflow:hidden;margin:0 auto}
.mine-avatar-v3 img{width:100%;height:100%;object-fit:cover;border-radius:50%}
.mine-edit-btn-v3{position:absolute;bottom:0;right:-4px;width:26px;height:26px;border-radius:50%;background:#fff;border:2px solid #06D6A0;color:#06D6A0;font-size:12px;display:flex;align-items:center;justify-content:center}
.mine-nickname-v3{color:#fff;font-size:20px;font-weight:700;margin:8px 0 4px}
.mine-level-v3{display:inline-block;background:rgba(255,255,255,.25);color:#fff;padding:2px 12px;border-radius:10px;font-size:12px}
.mine-progress-v3{margin:0 20px;background:#fff;border-radius:14px;padding:16px;box-shadow:0 2px 12px rgba(0,0,0,.08);transform:translateY(-20px)}
.mp-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.mp-label{font-size:13px;color:#666}.mp-value{font-size:13px;color:#06D6A0;font-weight:600}
.mp-bar{height:6px;background:#f0f0f0;border-radius:3px;overflow:hidden}
.mp-fill{height:100%;background:linear-gradient(90deg,#06D6A0,#0096C7);border-radius:3px;transition:width .3s}
.mp-flowers{display:flex;align-items:center;justify-content:flex-end;margin-top:6px;font-size:12px;color:#999}
.mp-flowers span{color:#06D6A0;font-weight:600;margin:0 2px}
.section-wrap-v3{margin:8px 16px}
.section-title-v3{font-size:12px;color:#999;padding:8px 4px 4px;font-weight:500}
.section-item-v3{display:flex;align-items:center;padding:13px 16px;background:#fff;cursor:pointer;border-bottom:1px solid #f5f5f5;font-size:14px;color:#2D2D2D;user-select:none}
.section-item-v3:active{background:#f9f9f9}
.section-item-v3:first-child{border-radius:14px 14px 0 0}
.section-item-v3:last-child{border-radius:0 0 14px 14px;border-bottom:none}
.section-item-v3:only-child{border-radius:14px}
.si-icon{width:28px;text-align:center;margin-right:12px;font-size:18px}
.si-text{flex:1}.si-extra{color:#999;font-size:12px;margin-right:8px}.si-arrow{color:#ccc;font-size:14px}
.logout-btn-v3{display:block;margin:24px auto;background:none;border:1px solid #ff4d4f;color:#ff4d4f;padding:10px 0;width:calc(100% - 32px);border-radius:14px;font-size:15px;cursor:pointer;text-align:center;background:#fff}
.logout-btn-v3:active{background:#fff5f5}
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
