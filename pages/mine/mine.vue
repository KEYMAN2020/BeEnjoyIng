<template>
<view class="pg">
  <view class="hd">
    <view class="sb">9:41</view>
    <view class="aw"><view class="av">
      <image v-if="avatarUrl" :src="avatarUrl" mode="aspectFill"/>
      <text v-else class="avf">👤</text>
    </view></view>
    <text class="nn">{{ nick || '未登录' }}</text>
    <text class="bio">热爱生活，喜欢运动</text>
    <view class="ss">
      <view class="si"><text class="sn">{{ sa }}</text><text class="sl">活动</text></view>
      <view class="si"><text class="sn">{{ sf }}</text><text class="sl">好友</text></view>
      <view class="si"><text class="sn">{{ sv }}</text><text class="sl">活力值</text></view>
    </view>
  </view>
  <view class="gd">
    <view class="gi" v-for="(it,i) in menu" :key="i" @click="tap(it.k)">
      <view class="gic" :style="{background:it.b,color:it.c}"><text>{{it.i}}</text></view>
      <text class="gl">{{it.l}}</text>
    </view>
  </view>
  <view style="height:80rpx"></view>
</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { request, hasToken, doLogin } from '@/utils/request.js'
const avatarUrl=ref(''),nick=ref('未登录'),sa=ref(0),sf=ref(0),sv=ref(0)
const menu=[
  {k:'act',i:'📋',b:'#E8F8F5',c:'#06D6A0',l:'我的活动'},{k:'fav',i:'⭐',b:'#FFF8E1',c:'#FFB800',l:'我的收藏'},
  {k:'fri',i:'👥',b:'#FFEBEE',c:'#FF6B6B',l:'我的好友'},{k:'ach',i:'🏆',b:'#FFF8E1',c:'#FFB800',l:'活力成就'},
  {k:'emg',i:'🆘',b:'#FFEBEE',c:'#FF6B6B',l:'紧急联系人'},{k:'heal',i:'📋',b:'#E8F8F5',c:'#06D6A0',l:'健康声明'},
  {k:'font',i:'A',b:'#E3F2FD',c:'#0096C7',l:'字体大小'},{k:'noti',i:'🔔',b:'#E3F2FD',c:'#0096C7',l:'消息通知'},
  {k:'pwd',i:'🔒',b:'#E3F2FD',c:'#0096C7',l:'修改密码'},{k:'prof',i:'👤',b:'#E3F2FD',c:'#0096C7',l:'个人信息'},
  {k:'priv',i:'🛡️',b:'#E3F2FD',c:'#0096C7',l:'隐私设置'},{k:'out',i:'🚪',b:'#FFEBEE',c:'#FF6B6B',l:'退出登录'}
]
onMounted(async()=>{
  if(!hasToken()){doLogin(()=>load());return}
  load()
})
async function load(){try{const r=await request({url:'/users/me'});if(r&&r.code===0){const u=r.data?.user||r.data||{};avatarUrl.value=u.avatar_url||'';nick.value=u.nickname||'未登录';const s=u.stats||{};sa.value=s.activity_count||0;sf.value=s.friends_count||0;sv.value=s.vitality||0}}catch(e){}}
function tap(k){if(k==='out'){uni.removeStorageSync('token');uni.showToast({title:'已退出',icon:'none'})}else{uni.showToast({title:'开发中',icon:'none'})}}
</script>

<style>
.pg{background:#F2F4F5;min-height:100vh;padding-bottom:160rpx}
.hd{background:linear-gradient(180deg,#06D6A0 0%,#0096C7 100%);padding:32rpx 40rpx 72rpx;text-align:center;border-radius:0 0 48rpx 48rpx}
.sb{color:#fff;font-size:30rpx;font-weight:600;margin-bottom:32rpx;text-align:left}
.aw{width:128rpx;height:128rpx;margin:0 auto 32rpx}
.av{width:128rpx;height:128rpx;border-radius:50%;border:6rpx solid rgba(255,255,255,.5);display:flex;align-items:center;justify-content:center;overflow:hidden;margin:0 auto;background:rgba(255,255,255,.2)}
.av image{width:100%;height:100%}.avf{font-size:64rpx}
.nn{color:#fff;font-size:36rpx;font-weight:700;margin-bottom:12rpx;display:block}
.bio{color:rgba(255,255,255,.8);font-size:26rpx;margin-bottom:40rpx;display:block}
.ss{display:flex;justify-content:center;gap:80rpx}
.si{text-align:center;color:#fff}.sn{font-size:40rpx;font-weight:700;display:block}.sl{font-size:24rpx;opacity:.8;margin-top:8rpx;display:block}
.gd{display:grid;grid-template-columns:repeat(4,1fr);gap:16rpx;padding:24rpx 32rpx}
.gi{background:#fff;border-radius:24rpx;padding:28rpx 12rpx;text-align:center;box-shadow:0 2rpx 8rpx rgba(0,0,0,.04)}
.gic{width:88rpx;height:88rpx;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 16rpx;font-size:40rpx}
.gl{font-size:24rpx;color:#333;font-weight:500;line-height:1.3}
</style>
