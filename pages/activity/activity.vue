<template>
<view class="pg">
  <view v-if="ld" class="sp"></view>
  <template v-else-if="d">
    <image v-if="d.cover_image" :src="d.cover_image" class="cv" mode="aspectFill"/>
    <view class="cd"><text class="tl">{{d.title}}</text>
      <view class="if"><view class="rw"><text>📅 {{(d.start_time||'').slice(0,16)}}</text></view>
        <view class="rw"><text>📍 {{d.city||d.location_name||'待定'}}</text></view>
        <view class="rw"><text>👥 {{d.current_participants||0}}/{{d.max_participants||'不限'}}人</text></view>
        <view class="rw" v-if="d.captain"><text>👨‍💼 队长：{{d.captain.nickname||d.captain_name||'待定'}}</text></view>
        <view class="rw"><text>💰 {{d.price>0?d.price+'元':'免费'}}</text></view>
      </view>
      <text class="cs" :style="{color:d.status_color||'#06D6A0',background:(d.status_color||'#06D6A0')+'18'}">{{d.status_text||(d.status==='open'?'进行中':d.status==='ended'?'已结束':'已解散')}}</text>
    </view>
    <view class="cd" v-if="d.description"><text class="lb">活动介绍</text><text class="dc">{{d.description}}</text></view>
    <view class="cd" v-if="d.tags&&d.tags.length"><text class="lb">标签</text><view class="tg"><text v-for="t in d.tags" :key="t" class="tgi">{{t}}</text></view></view>
    <view class="cd" v-if="d.requirements"><text class="lb">参加要求</text><text class="dc">{{d.requirements}}</text></view>
    <view class="act"><text class="btn" v-if="d.status==='open'" @click="signup">报名参加</text><text class="btn b2" @click="fav">收藏</text></view>
  </template>
</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { request } from '@/utils/request.js'
const d=ref(null),ld=ref(!0);let id=''
onMounted(()=>{const p=getCurrentPages();id=p[p.length-1].options?.id||'';if(!id){ld.value=!1;return};request({url:'/activities/'+id}).then(r=>{if(r.code===0)d.value=r.data?.activity||r.data;ld.value=!1}).catch(()=>ld.value=!1)})
function signup(){request({url:'/activities/'+id+'/signup',method:'POST'}).then(r=>uni.showToast({title:r.code===0?'报名成功':(r.message||'失败'),icon:'none'}))}
function fav(){request({url:'/activities/'+id+'/favorite',method:'POST'}).then(()=>uni.showToast({title:'已收藏',icon:'none'}))}
</script>

<style>.pg{background:#F2F4F5;min-height:100vh;padding-bottom:40rpx}
.sp{width:48rpx;height:48rpx;border:4rpx solid #ddd;border-top-color:#06D6A0;border-radius:50%;margin:200rpx auto;animation:spin .8s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
.cv{width:100%;height:400rpx}.cd{background:#fff;margin:16rpx 24rpx;border-radius:28rpx;padding:28rpx 32rpx}.tl{font-size:36rpx;font-weight:700;color:#1a1a1a;line-height:1.4}.if{margin-top:20rpx}.rw{padding:10rpx 0;font-size:28rpx;color:#666}.cs{display:inline-block;padding:6rpx 20rpx;border-radius:20rpx;font-size:24rpx;font-weight:600;margin-top:16rpx}.lb{font-size:30rpx;font-weight:600;color:#1a1a1a;margin-bottom:16rpx;display:block}.dc{font-size:28rpx;color:#666;line-height:1.6;display:block}.tg{display:flex;gap:12rpx;flex-wrap:wrap}.tgi{background:#E8F8F5;padding:8rpx 20rpx;border-radius:20rpx;font-size:24rpx;color:#06D6A0}.act{padding:24rpx}.btn{display:block;text-align:center;height:92rpx;line-height:92rpx;border-radius:24rpx;font-size:32rpx;font-weight:600;background:#06D6A0;color:#fff;margin-bottom:16rpx}.b2{background:#fff;color:#1a1a1a;border:2rpx solid #e0e0e0}</style>
