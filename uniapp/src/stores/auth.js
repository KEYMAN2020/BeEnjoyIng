import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI, userAPI } from '@/api/index.js'
export const useAuthStore = defineStore('auth',()=>{
  const token=ref(uni.getStorageSync('token')||''),user=ref(null),loading=ref(false)
  const isLoggedIn=computed(()=>!!token.value)
  async function login(phone,password){loading.value=true;try{const r=await authAPI.login({phone,password});token.value=r.data.token;uni.setStorageSync('token',r.data.token);user.value=r.data.user;return r}finally{loading.value=false}}
  async function fetchUser(){if(!token.value)return;try{const r=await userAPI.me();user.value=r.data}catch(e){}}
  function logout(){token.value='';user.value=null;uni.removeStorageSync('token');uni.reLaunch({url:'/pages/login/login'})}
  return{token,user,loading,isLoggedIn,login,fetchUser,logout}
})
