<template>
<view class="pg">
  <view class="hd"><view class="hr"><text class="ht">通讯录</text></view></view>
  <view class="sb"><view class="si"><text class="sii">🔍</text><input class="sip" placeholder="搜索"/></view></view>

  <view class="cc">
    <view class="ci"><view class="ca cr">👋</view><text class="cn">新的朋友</text><text v-if="pc>0" class="cb">{{pc>99?'99+':pc}}</text><text class="ar">›</text></view>
    <view class="ci"><view class="ca cg">👥</view><text class="cn">群聊</text><text class="ar">›</text></view>
  </view>

  <view class="cc2">
    <view v-if="ld" class="em">加载中...</view>
    <view v-else-if="friends.length===0" class="em">还没有好友</view>
    <block v-else v-for="g in grpList" :key="g.letter">
      <text class="cl">{{g.letter}}</text>
      <view v-for="f in g.members" :key="f.user_id||f.id" class="ci2">
        <view class="ca2"><image v-if="f.avatar_url" :src="f.avatar_url" mode="aspectFill"/><text v-else>{{(f.nickname||'?')[0]}}</text></view>
        <text class="fn">{{f.nickname}}</text>
      </view>
    </block>
  </view>
</view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { request, hasToken, doLogin } from '@/utils/request.js'

const friends=ref([]),ld=ref(!0),pc=ref(0)

onMounted(()=>{
  if(!hasToken()){doLogin(()=>loadAll());return}
  loadAll()
})

async function loadAll(){
  ld.value=!0
  try{
    const[fRes,pRes]=await Promise.all([request({url:'/users/friends'}),request({url:'/users/friends/requests/pending'})])
    if(fRes.code===0)friends.value=fRes.data?.friends||fRes.data||[]
    if(pRes.code===0)pc.value=Array.isArray(pRes.data)?pRes.data.length:0
  }catch(e){}
  ld.value=!1
}

const grpList=computed(()=>{
  const m={}
  friends.value.forEach(f=>{
    const l=((f.nickname||'#')[0]||'#').toUpperCase()
    if(!m[l])m[l]=[]
    m[l].push(f)
  })
  return Object.keys(m).sort().map(l=>({letter:l,members:m[l]}))
})
</script>

<style>.pg{background:#F2F4F5;min-height:100vh}
.hd{background:linear-gradient(180deg,#06D6A0 0%,#0096C7 100%);padding:24rpx 0 28rpx;text-align:center}.ht{color:#fff;font-size:34rpx;font-weight:600}
.sb{padding:16rpx 32rpx}.si{display:flex;align-items:center;gap:8rpx;background:#fff;border-radius:8rpx;height:72rpx;padding:0 20rpx}.sii{font-size:28rpx;opacity:.4}.sip{font-size:28rpx;color:#B0B0B0;flex:1}
.cc{background:#fff;margin:16rpx;border-radius:24rpx;padding:0 32rpx}.ci{display:flex;align-items:center;padding:28rpx 0;border-bottom:1rpx solid #f5f5f5}.ci:last-child{border-bottom:none}.ca{width:80rpx;height:80rpx;border-radius:16rpx;display:flex;align-items:center;justify-content:center;font-size:36rpx}.cr{background:#FFE8E0}.cg{background:#E0FFE8}.cn{font-size:30rpx;flex:1;margin-left:20rpx}.ar{font-size:36rpx;color:#ccc}.cb{background:#FF4757;color:#fff;font-size:20rpx;min-width:36rpx;height:36rpx;border-radius:18rpx;text-align:center;line-height:36rpx;padding:0 8rpx;margin-right:12rpx}
.cc2{background:#fff;margin:16rpx;border-radius:24rpx;padding:0 32rpx 16rpx}.cl{font-size:26rpx;color:#999;padding:20rpx 0 12rpx}.ci2{display:flex;align-items:center;padding:24rpx 0;border-bottom:1rpx solid #f5f5f5}.ci2:last-child{border-bottom:none}.ca2{width:80rpx;height:80rpx;border-radius:16rpx;display:flex;align-items:center;justify-content:center;font-size:36rpx;overflow:hidden;background:linear-gradient(135deg,#06D6A0,#0096C7);color:#fff}.ca2 image{width:100%;height:100%}.fn{font-size:30rpx;margin-left:20rpx}
.em{text-align:center;padding:80rpx 0;color:#999;font-size:28rpx}</style>
