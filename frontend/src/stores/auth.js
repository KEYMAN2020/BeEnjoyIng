import { defineStore } from 'pinia'
import { authAPI } from '@/api'
import router from '@/router'
export const useAuthStore = defineStore('auth', {
  state: () => ({ token: localStorage.getItem('token')||'', loading: false }),
  actions: {
    async login(phone,pw){ this.loading=true; try{ const r=await authAPI.login({phone,password:pw}); if(r.data.code===0){ this.token=r.data.data.access_token; localStorage.setItem('token',this.token); return {success:true} } return {success:false,message:r.data.message||'登录失败'} }catch(e){ return {success:false,message:'网络错误'} }finally{ this.loading=false } },
    async loginCode(d){ this.loading=true; try{ const r=await authAPI.loginCode(d); if(r.data.code===0){ this.token=r.data.data.access_token; localStorage.setItem('token',this.token); return {success:true} } return {success:false,message:r.data.message} }catch(e){ return {success:false,message:'网络错误'} }finally{ this.loading=false } },
    async register(d){ try{ const r=await authAPI.register(d); if(r.data.code===0) return {success:true}; return {success:false,message:r.data.message} }catch(e){ return {success:false,message:'网络错误'} } },
  }
})
