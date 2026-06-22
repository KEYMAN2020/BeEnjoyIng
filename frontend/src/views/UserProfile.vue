<template>
  <div class="profile-page-v3">
    <!-- Back bar -->
    <div class="pf-back">
      <button @click="$router.back()">‹</button>
      <span>用户资料</span>
      <button class="pf-edit-btn" @click="goEdit">编辑</button>
    </div>

    <div v-if="loading" class="empty-state">加载中...</div>
    <template v-else-if="profileInfo">
      <!-- Header -->
      <div class="pf-header">
        <div class="pf-avatar-lg">
          <img v-if="user.avatar_url" :src="user.avatar_url" @error="e => e.target.style.display='none'" />
          <span v-else>{{ (user.nickname || '?')[0] }}</span>
        </div>
        <div class="pf-name">{{ user.nickname }}</div>
        <div class="pf-phone">{{ user.phone }}</div>
      </div>

      <!-- 发消息按钮 -->
      <div class="pf-action-bar">
        <button class="pf-msg-btn" @click="$router.push('/chat/private/' + route.params.id)">
          💬 发消息
        </button>
      </div>

      <!-- Info Card -->
      <div class="pf-info-card">
        <div class="pf-row"><span class="pf-label">性别</span><span class="pf-val">{{ genderMap[profileInfo.gender] || profileInfo.gender || '未设置' }}</span></div>
        <div class="pf-row"><span class="pf-label">城市</span><span class="pf-val">{{ profileInfo.city || '未设置' }}</span></div>
        <div class="pf-row" v-if="profileInfo.district"><span class="pf-label">区县</span><span class="pf-val">{{ profileInfo.district }}</span></div>
        <div class="pf-row"><span class="pf-label">出生年份</span><span class="pf-val">{{ profileInfo.birth_year || '未设置' }}</span></div>
        <div class="pf-row"><span class="pf-label">真实姓名</span><span class="pf-val">{{ profileInfo.real_name || '未设置' }}</span></div>
        <div class="pf-row" v-if="profileInfo.interests">
          <span class="pf-label">兴趣</span>
          <div class="pf-tags">
            <span v-for="(tag, i) in profileInfo.interests.split(',')" :key="i" class="pf-tag" :style="{ background: tagColors[i % tagColors.length] }">{{ tag.trim() }}</span>
          </div>
        </div>
      </div>

      <!-- Privacy -->
      <div class="pf-divider"></div>
      <div class="pf-info-card">
        <div class="pf-row"><span class="pf-label">隐身模式</span><span class="pf-val">{{ profileInfo.ghost_mode ? '已开启' : '未开启' }}</span></div>
        <div class="pf-row"><span class="pf-label">允许私信</span><span class="pf-val">{{ profileInfo.allow_private_msg ? '已允许' : '未允许' }}</span></div>
        <div class="pf-row"><span class="pf-label">允许查看资料</span><span class="pf-val">{{ profileInfo.allow_profile_view ? '已允许' : '未允许' }}</span></div>
      </div>

      <!-- Stats -->
      <div class="pf-stats-card">
        <div class="pf-stats-grid">
          <div><div class="pf-stat-val">{{ stats?.vitality || 0 }}</div><div class="pf-stat-lbl">活力值</div></div>
          <div><div class="pf-stat-val">{{ stats?.activity_count || 0 }}</div><div class="pf-stat-lbl">活动</div></div>
          <div><div class="pf-stat-val">{{ stats?.friends_count || 0 }}</div><div class="pf-stat-lbl">好友</div></div>
          <div><div class="pf-stat-val">{{ stats?.activity_streak || 0 }}</div><div class="pf-stat-lbl">连续天数</div></div>
          <div><div class="pf-stat-val sm">{{ stats?.last_active_at ? stats.last_active_at.slice(0, 10) : '-' }}</div><div class="pf-stat-lbl">最近活跃</div></div>
          <div><div class="pf-stat-val sm">{{ user.role || 'user' }}</div><div class="pf-stat-lbl">角色</div></div>
        </div>
      </div>

      <!-- Bio -->
      <div class="pf-bio" v-if="profileInfo.bio">{{ profileInfo.bio }}</div>
    </template>
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

const genderMap = { male: '男', female: '女', other: '保密' }
const tagColors = ['#FF6B35', '#52c41a', '#1890ff', '#722ed1', '#eb2f96', '#13c2c2']

function goEdit() {
  router.push('/profile/edit')
}

onMounted(async () => {
  try {
    const profileId = route.params.id
    const [profileRes, statsRes] = await Promise.all([
      usersAPI.publicProfile(profileId),
      usersAPI.userStats(profileId)
    ])
    if (profileRes.data.code === 0) {
      const u = profileRes.data.data.user || profileRes.data.data || {}
      user.value = u
      profileInfo.value = u.profile || {}
    }
    if (statsRes.data.code === 0) stats.value = statsRes.data.data
  } catch (e) {}
  loading.value = false
})
</script>

<style scoped>
.profile-page-v3 { background: #f5f5f5; min-height: 100vh; padding-bottom: 80px; }
.pf-back { display: flex; align-items: center; padding: 12px 16px; background: #fff; border-bottom: 1px solid #f0f0f0; position: sticky; top: 0; z-index: 10; }
.pf-back button:first-child { background: none; border: none; color: #FF6B35; font-size: 28px; font-weight: 300; cursor: pointer; padding: 0 8px 0 0; line-height: 1; }
.pf-back span { flex: 1; text-align: center; font-size: 16px; font-weight: 700; color: #2D2D2D; }
.pf-edit-btn { border: 1px solid #FF6B35 !important; color: #FF6B35 !important; background: #fff !important; padding: 4px 14px !important; border-radius: 14px !important; font-size: 13px !important; cursor: pointer; margin-left: 8px; }

.pf-header { background: linear-gradient(135deg, #FF6B35, #FF8A50); padding: 30px 20px 40px; text-align: center; border-radius: 0 0 24px 24px; }
.pf-avatar-lg { width: 80px; height: 80px; border-radius: 50%; background: #fff; color: #FF6B35; font-size: 36px; font-weight: 700; display: flex; align-items: center; justify-content: center; margin: 0 auto 12px; overflow: hidden; }
.pf-avatar-lg img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }
.pf-name { color: #fff; font-size: 22px; font-weight: 700; }
.pf-phone { color: rgba(255,255,255,.7); font-size: 13px; margin-top: 4px; }

.pf-action-bar { padding: 12px 16px; margin-top: -20px; position: relative; z-index: 5; }
.pf-msg-btn {
  width: 100%; padding: 12px 0; background: #07C160; color: #fff;
  border: none; border-radius: 12px; font-size: 16px; font-weight: 600;
  cursor: pointer; box-shadow: 0 2px 8px rgba(7,193,96,.3);
}
.pf-msg-btn:active { opacity: 0.85; }

.pf-info-card { margin: 12px 16px; background: #fff; border-radius: 14px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,.06); }
.pf-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #f5f5f5; font-size: 14px; }
.pf-row:last-child { border-bottom: none; }
.pf-label { color: #999; }
.pf-val { color: #2D2D2D; text-align: right; max-width: 60%; }
.pf-tags { display: flex; flex-wrap: wrap; gap: 6px; justify-content: flex-end; max-width: 60%; }
.pf-tag { display: inline-block; padding: 3px 10px; border-radius: 10px; font-size: 12px; color: #fff; }
.pf-divider { padding: 0 16px; margin: 0 16px 12px; }
.pf-divider::after { content: ''; display: block; height: 1px; background: #f0f0f0; }

.pf-stats-card { margin: 0 16px 12px; background: #fff; border-radius: 14px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,.04); }
.pf-stats-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; text-align: center; }
.pf-stat-val { font-size: 22px; font-weight: 700; color: #FF6B35; }
.pf-stat-val.sm { font-size: 13px; }
.pf-stat-lbl { font-size: 11px; color: #999; margin-top: 2px; }

.pf-bio { margin: 0 16px 12px; background: #fff; border-radius: 14px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,.04); font-size: 14px; color: #666; line-height: 1.6; }
.empty-state { text-align: center; color: #999; padding: 60px 20px; font-size: 14px; }
</style>
