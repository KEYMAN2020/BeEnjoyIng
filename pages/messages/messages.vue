<template>
<view class="pg">
  <view class="hd"><view class="hr"><text class="ht">消息</text><text class="hp" @click="showAct=!showAct">＋</text></view></view>

  <view class="sb"><view class="si"><text class="sii">🔍</text><text class="sit">搜索</text></view></view>

  <view class="ml">
    <view v-if="loading" class="em">加载中...</view>
    <view v-else-if="merged.length===0" class="em">
      <text class="ei">💬</text><text class="et">暂无消息</text><text class="eh">和好友聊聊天吧</text>
    </view>
    <view v-else v-for="m in merged" :key="m._key" class="mi" @click="go(m)">
      <view class="mw">
        <view class="ma"><image v-if="m._avatar" :src="m._avatar" mode="aspectFill"/><text v-else>{{m._initial}}</text></view>
        <text v-if="m._unread>0" class="mb">{{m._unread>99?'99+':m._unread}}</text>
      </view>
      <view class="mc"><view class="mr"><text class="mn">{{m._name}}</text><text class="mt">{{m._time}}</text></view><text class="mp">{{m._preview}}</text></view>
    </view>
  </view>
</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { request, hasToken, doLogin } from '@/utils/request.js'

const groups=ref([]),privates=ref([]),loading=ref(!0),showAct=ref(!1),merged=ref([])

function fmtTime(ts){
  if(!ts)return'';const d=new Date(ts);if(isNaN(d.getTime()))return''
  const n=new Date(),td=new Date(n.getFullYear(),n.getMonth(),n.getDate()),md=new Date(d.getFullYear(),d.getMonth(),d.getDate())
  const diff=Math.floor((td-md)/86400000)
  if(diff===0)return d.toTimeString().slice(0,5)
  if(diff===1)return'昨天'
  if(diff<7){const days=['周日','周一','周二','周三','周四','周五','周六'];return days[d.getDay()]}
  return(d.getMonth()+1)+'月'+d.getDate()+'日'
}

function buildMerged(){
  const list=[]
  if(Array.isArray(groups.value)){groups.value.forEach(g=>{list.push({_key:'g-'+g.id,_type:'group',_name:g.name||'群聊',_avatar:g.avatar||'',_initial:(g.name||'群')[0],_preview:g.last_message||'暂无消息',_time:fmtTime(g.last_message_at),_sortTime:g.last_message_at?new Date(g.last_message_at).getTime():0,_unread:g.unread||g.unread_count||0,_targetId:g.id})})}
  if(Array.isArray(privates.value)){privates.value.forEach(p=>{const o=p.other_user||{};list.push({_key:'p-'+(o.user_id||p.message_id),_type:'private',_name:o.nickname||'用户',_avatar:o.avatar_url||'',_initial:(o.nickname||'?')[0],_preview:p.content||'暂无消息',_time:fmtTime(p.created_at),_sortTime:p.created_at?new Date(p.created_at).getTime():0,_unread:p.is_read?0:1,_targetId:o.user_id})})}
  list.sort((a,b)=>(b._sortTime||0)-(a._sortTime||0))
  return list
}

async function loadData(){
  if(!hasToken()){loading.value=!1;merged.value=[];return}
  try{
    const[gRes,pRes]=await Promise.all([request({url:'/chat/groups'}),request({url:'/users/messages'})])
    if(gRes.code===0){groups.value=gRes.data?.groups||gRes.data||[]}
    if(pRes.code===0){privates.value=Array.isArray(pRes.data)?pRes.data:(pRes.data?.items||pRes.data?.conversations||[])}
    merged.value=buildMerged()
  }catch(e){}finally{loading.value=!1}
}

function go(m){
  if(m._type==='group')uni.navigateTo({url:'/pages/chat/chat?gid='+m._targetId})
  else uni.navigateTo({url:'/pages/messages/messages'})
}

onMounted(()=>{
  if(!hasToken()){doLogin(()=>loadData());return}
  loadData()
})
</script>

<style>.pg{background:#F2F4F5;min-height:100vh}
.hd{background:linear-gradient(180deg,#06D6A0 0%,#0096C7 100%);padding:24rpx 0 28rpx;text-align:center}.hr{position:relative}.ht{color:#fff;font-size:34rpx;font-weight:600}.hp{position:absolute;right:32rpx;top:0;color:#fff;font-size:44rpx;font-weight:300}
.sb{padding:16rpx 32rpx}.si{display:flex;align-items:center;justify-content:center;gap:8rpx;background:#fff;border-radius:8rpx;height:72rpx;padding:0 20rpx}.sii{font-size:28rpx;opacity:.4}.sit{font-size:28rpx;color:#B0B0B0}
.ml{background:#fff;margin:0 32rpx;border-radius:24rpx;overflow:hidden}
.mi{display:flex;align-items:center;gap:24rpx;padding:24rpx 32rpx;border-bottom:1rpx solid #f5f5f5}.mi:last-child{border-bottom:none}
.mw{position:relative;flex-shrink:0}.ma{width:96rpx;height:96rpx;border-radius:16rpx;display:flex;align-items:center;justify-content:center;font-size:40rpx;color:#fff;overflow:hidden;background:linear-gradient(135deg,#06D6A0,#0096C7)}.ma image{width:100%;height:100%}
.mb{position:absolute;top:-8rpx;right:-8rpx;background:#FF6B6B;color:#fff;font-size:22rpx;min-width:36rpx;height:36rpx;border-radius:18rpx;display:flex;align-items:center;justify-content:center;padding:0 10rpx;font-weight:600}
.mc{flex:1;overflow:hidden}.mr{display:flex;justify-content:space-between;align-items:center}.mn{font-size:32rpx;color:#333}.mt{font-size:24rpx;color:#999}.mp{margin-top:8rpx;font-size:28rpx;color:#999;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.em{text-align:center;padding:120rpx 0;color:#999}.ei{font-size:96rpx;display:block;margin-bottom:24rpx}.et{font-size:30rpx;display:block;margin-bottom:16rpx}.eh{font-size:26rpx;color:#bbb}
</style>
