<template>
  <div class="up-page">
    <!-- ═══ Teal Header ═══ -->
    <div class="up-header">
      <div class="up-header-row">
        <span class="up-back" @click="$router.back()">←</span>
        <span class="up-title">用户资料</span>
        <span v-if="isSelf" class="up-edit" @click="goEdit">编辑</span>
        <span v-else style="width:36px"></span>
      </div>
      <div class="up-avatar-wrap">
        <div class="up-avatar">
          <img v-if="user.avatar_url" :src="user.avatar_url" @error="e=>e.target.style.display='none'" />
          <span v-else>{{ (user.nickname||'?')[0] }}</span>
        </div>
        <div class="up-name">{{ user.nickname }}</div>
        <div class="up-phone">{{ user.phone }}</div>
      </div>
    </div>

    <!-- ═══ Loading ═══ -->
    <div v-if="loading" class="up-empty">加载中...</div>

    <template v-else-if="profileInfo">
      <!-- ═══ Action Buttons ═══ -->
      <div class="up-actions">
        <button class="up-msg-btn" @click="$router.push('/chat/private/' + route.params.id)">💬 发消息</button>
        <button v-if="!isSelf && isFriend" class="up-del-btn" @click="confirmDelete">🗑️ 删除好友</button>
      </div>

      <!-- ═══ Info Card ═══ -->
      <div class="up-card">
        <div class="up-row"><span class="up-label">性别</span><span class="up-val">{{ genderMap[profileInfo.gender] || '未设置' }}</span></div>
        <div class="up-row"><span class="up-label">城市</span><span class="up-val">{{ profileInfo.city || '未设置' }}</span></div>
        <div class="up-row" v-if="profileInfo.district"><span class="up-label">区县</span><span class="up-val">{{ profileInfo.district }}</span></div>
        <div class="up-row"><span class="up-label">出生年份</span><span class="up-val">{{ profileInfo.birth_year || '未设置' }}</span></div>
        <div class="up-row"><span class="up-label">真实姓名</span><span class="up-val">{{ profileInfo.real_name || '未设置' }}</span></div>
        <div class="up-row" v-if="profileInfo.interests">
          <span class="up-label">兴趣</span>
          <div class="up-tags">
            <span v-for="(tag,i) in profileInfo.interests.split(',')" :key="i" class="up-tag" :style="{background:tagColors[i%6]}">{{ tag.trim() }}</span>
          </div>
        </div>
      </div>

      <!-- ═══ Privacy Card ═══ -->
      <div class="up-card">
        <div class="up-row"><span class="up-label">隐身模式</span><span class="up-val">{{ profileInfo.ghost_mode ? '已开启' : '未开启' }}</span></div>
        <div class="up-row"><span class="up-label">允许私信</span><span class="up-val">{{ profileInfo.allow_private_msg ? '已允许' : '未允许' }}</span></div>
        <div class="up-row"><span class="up-label">允许查看资料</span><span class="up-val">{{ profileInfo.allow_profile_view ? '已允许' : '未允许' }}</span></div>
      </div>

      <!-- ═══ Stats ═══ -->
      <div class="up-card up-stats">
        <div class="up-stat"><div class="up-stat-num">{{ stats?.vitality||0 }}</div><div class="up-stat-lbl">活力值</div></div>
        <div class="up-stat"><div class="up-stat-num">{{ stats?.activity_count||0 }}</div><div class="up-stat-lbl">活动</div></div>
        <div class="up-stat"><div class="up-stat-num">{{ stats?.friends_count||0 }}</div><div class="up-stat-lbl">好友</div></div>
        <div class="up-stat"><div class="up-stat-num sm">{{ stats?.activity_streak||0 }}</div><div class="up-stat-lbl">连续天数</div></div>
        <div class="up-stat"><div class="up-stat-num sm">{{ stats?.last_active_at ? stats.last_active_at.slice(0,10) : '-' }}</div><div class="up-stat-lbl">最近活跃</div></div>
        <div class="up-stat"><div class="up-stat-num sm">{{ user.role||'user' }}</div><div class="up-stat-lbl">角色</div></div>
      </div>

      <!-- ═══ Bio ═══ -->
      <div class="up-card up-bio" v-if="profileInfo.bio">{{ profileInfo.bio }}</div>
    </template>

    <!-- ═══ Delete Confirm ═══ -->
    <div v-if="showDeleteConfirm" class="up-modal-bg" @click.self="showDeleteConfirm=false">
      <div class="up-modal-box">
        <p>确定要删除「<b>{{ user.nickname }}</b>」吗？</p>
        <p style="font-size:12px;color:#999;margin-top:4px">删除后将不再显示对方的消息</p>
        <div class="up-modal-row">
          <button class="up-btn-c" @click="showDeleteConfirm=false">取消</button>
          <button class="up-btn-d" @click="deleteFriend">删除</button>
        </div>
      </div>
    </div>

    <div style="height:60px"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usersAPI } from '@/api'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const user = ref({})
const profileInfo = ref(null)
const stats = ref(null)
const showDeleteConfirm = ref(false)
const isFriend = ref(false)
const isSelf = ref(false)

const genderMap = { male:'男', female:'女', other:'保密' }
const tagColors = ['#06D6A0','#FFB800','#0096C7','#FF6B6B','#722ED1','#FF85C0']

function goEdit() { router.push('/profile/edit') }

async function checkFriendship() {
  try {
    const res = await usersAPI.friends()
    if (res.data?.code === 0) {
      const targetId = parseInt(route.params.id)
      const friends = res.data.data.items || []
      isFriend.value = friends.some(f => f.user_id == targetId || f.friend_id == targetId)
    }
  } catch(e) {}
  try {
    const ui = localStorage.getItem('user_info')
    if (ui) { const u = JSON.parse(ui); isSelf.value = u.user_id == route.params.id }
  } catch(e) {}
}

function confirmDelete() { showDeleteConfirm.value = true }

async function deleteFriend() {
  try {
    const res = await usersAPI.removeFriend(route.params.id)
    if (res.data?.code === 0) { alert('已删除好友'); showDeleteConfirm.value = false; router.back() }
    else alert(res.data?.message || '删除失败')
  } catch(e) { alert('操作失败') }
}

onMounted(async () => {
  checkFriendship()
  try {
    const profileId = route.params.id
    const [profileRes, statsRes] = await Promise.all([usersAPI.publicProfile(profileId), usersAPI.userStats(profileId)])
    if (profileRes.data?.code === 0) {
      const u = profileRes.data.data.user || profileRes.data.data || {}
      user.value = u; profileInfo.value = u.profile || {}
    }
    if (statsRes.data?.code === 0) stats.value = statsRes.data.data
  } catch(e) {}
  loading.value = false
})
</script>

<style scoped>
.up-page { background: #F2F4F5; min-height: 100vh; font-family: 'PingFang SC', sans-serif }

/* Header */
.up-header { background: linear-gradient(180deg, #06D6A0 0%, #0096C7 100%); padding: 12px 0 24px }
.up-header-row { display: flex; align-items: center; padding: 0 16px; margin-bottom: 20px }
.up-back { color: #fff; font-size: 18px; cursor: pointer; width: 36px }
.up-title { flex: 1; text-align: center; color: #fff; font-size: 17px; font-weight: 600 }
.up-edit { color: #fff; font-size: 14px; cursor: pointer; width: 36px; text-align: right; border: 1px solid rgba(255,255,255,.5); border-radius: 12px; padding: 2px 10px; width: auto }
.up-avatar-wrap { text-align: center }
.up-avatar { width: 72px; height: 72px; border-radius: 50%; background: rgba(255,255,255,.3); display: flex; align-items: center; justify-content: center; margin: 0 auto 10px; font-size: 32px; color: #fff; overflow: hidden }
.up-avatar img { width: 100%; height: 100%; object-fit: cover; border-radius: 50% }
.up-name { color: #fff; font-size: 20px; font-weight: 700 }
.up-phone { color: rgba(255,255,255,.75); font-size: 13px; margin-top: 4px }

/* Actions */
.up-actions { padding: 12px 16px }
.up-msg-btn { width: 100%; padding: 12px; background: #06D6A0; color: #fff; border: none; border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer; box-shadow: 0 2px 8px rgba(6,214,160,.3) }
.up-msg-btn:active { opacity: .85 }
.up-del-btn { width: 100%; padding: 12px; background: #fff; color: #FF6B6B; border: 1px solid #FF6B6B; border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer; margin-top: 10px }

/* Cards */
.up-card { background: #fff; border-radius: 12px; margin: 0 16px 10px; padding: 8px 0; box-shadow: 0 1px 4px rgba(0,0,0,.04); overflow: hidden }
.up-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #f5f5f5; font-size: 14px }
.up-row:last-child { border-bottom: none }
.up-label { color: #999; flex-shrink: 0 }
.up-val { color: #333; text-align: right; max-width: 60% }
.up-tags { display: flex; flex-wrap: wrap; gap: 6px; justify-content: flex-end; max-width: 60% }
.up-tag { padding: 3px 10px; border-radius: 10px; font-size: 12px; color: #fff }

/* Stats */
.up-stats { display: grid; grid-template-columns: repeat(3,1fr); gap: 4px 0; padding: 16px }
.up-stat { text-align: center; padding: 8px 4px }
.up-stat-num { font-size: 22px; font-weight: 700; color: #0096C7 }
.up-stat-num.sm { font-size: 13px }
.up-stat-lbl { font-size: 11px; color: #999; margin-top: 2px }

/* Bio */
.up-bio { padding: 16px; font-size: 14px; color: #666; line-height: 1.6 }

/* Modal */
.up-modal-bg { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,.45); z-index: 999; display: flex; align-items: center; justify-content: center }
.up-modal-box { width: 280px; background: #fff; border-radius: 16px; padding: 24px 20px; text-align: center }
.up-modal-box p { margin: 0 0 8px; font-size: 15px; color: #333; line-height: 1.5 }
.up-modal-row { display: flex; gap: 12px; margin-top: 20px }
.up-btn-c { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 10px; background: #fff; color: #666; font-size: 15px; cursor: pointer }
.up-btn-d { flex: 1; padding: 10px; border: none; border-radius: 10px; background: #FF6B6B; color: #fff; font-size: 15px; cursor: pointer }

/* Empty */
.up-empty { text-align: center; padding: 60px; color: #999; font-size: 14px }
</style>
