<template>
<view class="pg">
  <view class="fm">
    <view class="fg"><text class="lb">活动标题 *</text><input class="in" v-model="f.title" placeholder="给活动取个名字"/></view>
    <view class="fg"><text class="lb">活动分类 *</text><picker :range="catN" @change="e=>f.category_id=cats[e.detail.value]?.id||''"><text class="in" :class="{ph:!f.category_id}">{{catN[f.category_id]||'请选择'}}</text></picker></view>
    <view class="fg"><text class="lb">开始时间 *</text><picker mode="date" :value="f.start_time" @change="e=>f.start_time=e.detail.value"><text class="in" :class="{ph:!f.start_time}">{{f.start_time||'选择日期'}}</text></picker></view>
    <view class="fg"><text class="lb">活动地点 *</text><input class="in" v-model="f.location_name" placeholder="输入地址"/></view>
    <view class="fg"><text class="lb">人数限制</text><input class="in" v-model="f.max_participants" type="number" placeholder="不填不限制"/></view>
    <view class="fg"><text class="lb">费用 (元)</text><input class="in" v-model="f.price" type="digit" placeholder="0 = 免费"/></view>
    <view class="fg"><text class="lb">活动描述</text><textarea class="ta" v-model="f.description" placeholder="介绍一下活动内容..."/></view>
    <view class="fg"><text class="lb">参加要求</text><input class="in" v-model="f.requirements" placeholder="例如：需自备装备"/></view>
    <text class="btn" @click="submit">发起活动</text>
  </view>
</view>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { request } from '@/utils/request.js'
const f=reactive({title:'',category_id:'',start_time:'',location_name:'',max_participants:null,price:0,description:'',requirements:''})
const cats=ref([]),catN={}
onMounted(async()=>{try{const r=await request({url:'/activities/categories'});if(r.code===0&&r.data){(r.data.categories||r.data||[]).forEach(c=>{catN[c.id]=c.name});cats.value=r.data.categories||r.data||[]}}catch(e){}})
async function submit(){if(!f.title||!f.start_time||!f.location_name)return uni.showToast({title:'请填写必填项',icon:'none'});const r=await request({url:'/activities',method:'POST',data:{title:f.title,category_id:f.category_id,start_time:f.start_time,location_name:f.location_name,max_participants:f.max_participants?Number(f.max_participants):null,price:f.price?Number(f.price):0,description:f.description,requirements:f.requirements}});uni.showToast({title:r.code===0?'创建成功':(r.message||'失败'),icon:'none'});if(r.code===0)setTimeout(()=>uni.switchTab({url:'/pages/index/index'}),1200)}
</script>

<style>.pg{background:#F2F4F5;min-height:100vh}.fm{padding:24rpx}.fg{margin-bottom:28rpx}.lb{font-size:28rpx;font-weight:600;color:#1a1a1a;margin-bottom:12rpx;display:block}.in{background:#fff;padding:20rpx 24rpx;border-radius:16rpx;font-size:28rpx;border:2rpx solid #e0e0e0;color:#1a1a1a}.ph{color:#999}.ta{background:#fff;padding:20rpx 24rpx;border-radius:16rpx;font-size:28rpx;border:2rpx solid #e0e0e0;width:100%;min-height:200rpx}.btn{display:block;text-align:center;width:100%;height:96rpx;line-height:96rpx;margin-top:36rpx;background:#06D6A0;color:#fff;font-size:32rpx;font-weight:700;border-radius:24rpx}</style>
