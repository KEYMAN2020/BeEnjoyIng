<template>
<view class="pg">
  <view class="hd"><view class="hr"><text class="ht">发现活动</text></view></view>
  <scroll-view scroll-x class="tw"><view class="ti"><text class="tb on">全部</text><text v-for="c in cats" :key="c.id" class="tb">{{c.name}}</text></view></scroll-view>
  <view v-if="loading" class="em">加载中...</view>
  <view v-else>
    <view v-for="a in list" :key="a.id" class="cd" @click="go(a.id)">
      <view class="cb"><text class="ctl">{{a.title}}</text>
        <view class="cm"><text>{{fmt(a.start_time)}}</text><text>{{a.city||a.location_name}}</text></view>
        <view class="cf"><text class="cs">{{a.status_text||'进行中'}}</text><text>{{a.current_participants||0}}人</text></view>
      </view>
    </view>
    <view v-if="list.length===0" class="em">暂无活动</view>
  </view>
</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { request, doLogin } from '@/utils/request.js'
const list=ref([]),cats=ref([]),loading=ref(!0)
async function load(){
  loading.value=!0
  try{const r=await request({url:'/activities',data:{per_page:20}});if(r.code===0){const d=r.data||r;list.value=d.activities||d||[]}}catch(e){}finally{loading.value=!1}
}
onMounted(()=>{load();setTimeout(async()=>{try{const r=await request({url:'/activities/categories'});if(r.code===0)cats.value=r.data?.categories||r.data||[]}catch(e){}},500)})
function fmt(d){if(!d)return'';const dt=new Date(d);return(dt.getMonth()+1)+'月'+dt.getDate()+'日'}
function go(id){doLogin(()=>{uni.navigateTo({url:'/pages/activity/activity?id='+id})})}
</script>

<style>.pg{background:#F2F4F5;min-height:100vh}.hd{background:linear-gradient(180deg,#06D6A0 0%,#0096C7 100%);padding:48rpx 32rpx 28rpx}.ht{flex:1;color:#fff;font-size:36rpx;font-weight:700}.tw{background:#fff;white-space:nowrap;padding:20rpx 32rpx}.ti{display:flex;gap:16rpx}.tb{padding:14rpx 28rpx;border-radius:36rpx;font-size:28rpx;color:#666;background:#F2F4F5}.tb.on{background:#06D6A0;color:#fff;font-weight:600}.cd{background:#fff;margin:16rpx 24rpx;border-radius:16rpx;overflow:hidden}.cb{padding:24rpx}.ctl{font-size:32rpx;font-weight:600;color:#1a1a1a;display:block}.cm{margin-top:12rpx;font-size:24rpx;color:#999;display:flex;gap:16rpx}.cf{display:flex;justify-content:space-between;margin-top:12rpx;font-size:24rpx;color:#999}.cs{padding:2rpx 14rpx;background:#e8fff5;color:#06D6A0;border-radius:6rpx;font-size:22rpx}.em{text-align:center;padding:120rpx 0;color:#999}</style>
