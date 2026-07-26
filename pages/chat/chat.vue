<template>
<view class="pg">
  <view class="hd"><text class="hdb" @click="uni.navigateBack()">‹</text><text class="hdt">{{gn}}{{mc>0?' ('+mc+')':''}}</text><view class="hdr"></view></view>
  <scroll-view scroll-y class="ml" :scroll-into-view="sv" scroll-with-animation>
    <view v-if="ld" class="sp"></view>
    <template v-else>
      <view v-for="(m,i) in msgs" :key="m.id||i">
        <view class="td" v-if="showTd(m,i)">{{fmt(m.created_at)}}</view>
        <view class="mr" :class="{mine:isM(m)}">
          <view class="ma" v-if="!isM(m)"><image v-if="m.avatar_url" :src="m.avatar_url" mode="aspectFill"/><text v-else>{{(m.nickname||'?')[0]}}</text></view>
          <view class="mb" :class="{bmo:!isM(m),bmm:isM(m)}"><text class="mbs" v-if="!isM(m)&&m.nickname">{{m.nickname}}</text><text>{{m.content}}</text></view>
        </view>
      </view>
    </template>
  </scroll-view>
  <view class="ib"><input class="ci" v-model="txt" placeholder="输入消息..." confirm-type="send" @confirm="send"/><text class="sb" @click="send">发送</text></view>
</view>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { request } from '@/utils/request.js'
const msgs=ref([]),txt=ref(''),sv=ref(''),ld=ref(!0),gn=ref(''),mc=ref(0);let gid='',uid=0
onMounted(async()=>{const p=getCurrentPages();gid=p[p.length-1].options?.gid;if(!gid){ld.value=!1;return};try{const r=await request({url:'/chat/groups/'+gid+'/messages'});if(r.code===0&&r.data){gn.value=r.data.group_name||'';mc.value=r.data.member_count||0;msgs.value=Array.isArray(r.data.messages)?r.data.messages:(r.data||[])}}catch(e){};try{const t=uni.getStorageSync('token');if(t)uid=JSON.parse(atob(t.split('.')[1])).user_id}catch(e){};ld.value=!1})
function isM(m){return m.sender_id===uid||m.user_id===uid}
function showTd(m,i){if(i===0)return!0;const p=msgs.value[i-1];return !p||new Date(m.created_at||m.time)-new Date(p.created_at||p.time)>60000}
function fmt(d){if(!d)return'';const dt=new Date(d);return dt.getMonth()+1+'月'+dt.getDate()+'日 '+String(dt.getHours()).padStart(2,'0')+':'+String(dt.getMinutes()).padStart(2,'0')}
async function send(){if(!txt.value.trim())return;const c=txt.value.trim();txt.value='';msgs.value.push({id:Date.now(),sender_id:uid,content:c,created_at:new Date().toISOString()});await nextTick();sv.value='m-'+msgs.value[msgs.value.length-1].id;await request({url:'/chat/groups/'+gid+'/messages',method:'POST',data:{content:c,type:'text'}})}
</script>

<style>.pg{display:flex;flex-direction:column;height:100vh;background:#EDEDED}
.hd{display:flex;align-items:center;padding:24rpx 24rpx;background:#EDEDED;border-bottom:1rpx solid #d9d9d9;height:88rpx}.hdb{font-size:48rpx;color:#000;width:60rpx}.hdt{flex:1;text-align:center;font-size:34rpx;font-weight:500}.hdr{width:60rpx}
.ml{flex:1;padding:16rpx 24rpx}.sp{width:48rpx;height:48rpx;border:4rpx solid #ddd;border-top-color:#06D6A0;border-radius:50%;margin:200rpx auto;animation:spin .8s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
.td{text-align:center;padding:16rpx 0;font-size:22rpx;color:#999}
.mr{display:flex;margin-bottom:24rpx;align-items:flex-start}.mr.mine{flex-direction:row-reverse}.ma{width:72rpx;height:72rpx;border-radius:50%;overflow:hidden;display:flex;align-items:center;justify-content:center;background:#E8F8F5;font-size:28rpx;color:#06D6A0;flex-shrink:0}.ma image{width:100%;height:100%}.mr.mine .ma{display:none}
.mb{max-width:480rpx;padding:18rpx 24rpx;border-radius:12rpx;font-size:30rpx;line-height:1.4}.bmo{background:#fff;margin-left:16rpx}.bmm{background:#06D6A0;color:#fff}.mbs{font-size:22rpx;color:#91d5ff;margin-bottom:6rpx}
.ib{display:flex;padding:16rpx 24rpx;background:#f5f5f5;border-top:1rpx solid #e0e0e0;align-items:center}.ci{flex:1;height:72rpx;background:#fff;border-radius:36rpx;padding:0 28rpx;font-size:30rpx}.sb{margin-left:16rpx;padding:16rpx 32rpx;background:#06D6A0;color:#fff;font-size:28rpx;border-radius:12rpx}
</style>
