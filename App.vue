<script>
import { request } from '@/utils/request.js'
export default {
  onLaunch(){
    const t=uni.getStorageSync('token')
    if(t){
      request({url:'/users/me'}).then(r=>{if(r.code===0)console.log('已登录')}).catch(()=>{uni.removeStorageSync('token')})
    }
  }
}
</script>
<style>page{background:#F2F4F5}</style>
