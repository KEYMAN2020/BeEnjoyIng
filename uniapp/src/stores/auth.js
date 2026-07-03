import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { authAPI, usersAPI } from "@/api/index.js"

export const useAuthStore = defineStore("auth", () => {
  const token = ref(uni.getStorageSync("token") || "")
  const user = ref(null)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!token.value)

  async function login(phone, password) {
    loading.value = true
    try {
      const res = await authAPI.login({ phone, password })
      const d = res.data
      if (d.code === 0) {
        token.value = d.data.access_token
        uni.setStorageSync("token", token.value)
        await fetchUser()
        return { success: true }
      }
      return { success: false, message: d.message || "登录失败" }
    } catch (err) {
      return { success: false, message: err.response?.data?.message || "网络错误" }
    } finally { loading.value = false }
  }

  async function register(data) {
    loading.value = true
    try {
      const res = await authAPI.register(data)
      const d = res.data
      if (d.code === 0) return { success: true }
      return { success: false, message: d.message || "注册失败" }
    } catch (err) {
      return { success: false, message: err.response?.data?.message || "网络错误" }
    } finally { loading.value = false }
  }

  async function fetchUser() {
    try {
      const res = await usersAPI.me()
      if (res.data.code === 0) user.value = res.data.data
    } catch (err) { console.error("fetchUser:", err) }
  }

  function logout() {
    token.value = ""
    user.value = null
    uni.removeStorageSync("token")
    authAPI.logout().catch(() => {})
  }

  return { token, user, loading, isLoggedIn, login, register, fetchUser, logout }
})
