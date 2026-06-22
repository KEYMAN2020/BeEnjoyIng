<template>
  <div class="auth-page">
    <div class="auth-header">
      <h1>🏕️ 银发活力</h1>
      <p>发现身边的活动，开启精彩晚年生活</p>
    </div>

    <div class="auth-tabs">
      <button :class="{ active: mode === 'password' }" @click="mode = 'password'">密码登录</button>
      <button :class="{ active: mode === 'code' }" @click="mode = 'code'">验证码登录</button>
    </div>

    <form class="auth-form" @submit.prevent="handleLogin">
      <div class="form-group">
        <label>手机号</label>
        <input v-model="phone" type="tel" maxlength="11" placeholder="请输入手机号" />
      </div>

      <div class="form-group" v-if="mode === 'password'">
        <label>密码</label>
        <input v-model="password" type="password" placeholder="请输入密码" />
      </div>

      <div class="form-group" v-if="mode === 'code'">
        <label>验证码</label>
        <div style="display:flex;gap:8px">
          <input v-model="code" type="text" maxlength="6" placeholder="请输入验证码" style="flex:1" />
          <button type="button" class="btn btn-outline btn-sm" @click="sendCode" :disabled="countdown > 0" style="white-space:nowrap">
            {{ countdown > 0 ? `${countdown}s` : "获取验证码" }}
          </button>
        </div>
      </div>

      <div class="form-error" v-if="error">{{ error }}</div>

      <button type="submit" class="btn btn-primary btn-block" :disabled="auth.loading" style="margin-top:16px">
        {{ auth.loading ? "登录中..." : "登录" }}
      </button>
    </form>

    <div class="auth-footer">
      <router-link to="/register">还没有账号？立即注册</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { useRouter, useRoute } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { authAPI } from "@/api"

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const mode = ref("password")
const phone = ref("")
const password = ref("")
const code = ref("")
const error = ref("")
const countdown = ref(0)

async function sendCode() {
  if (!phone.value || phone.value.length < 11) { error.value = "请输入正确的手机号"; return }
  try {
    await authAPI.sendCode({ phone: phone.value })
    countdown.value = 60
    const timer = setInterval(() => { countdown.value--; if (countdown.value <= 0) clearInterval(timer) }, 1000)
    error.value = ""
  } catch (e) { error.value = e.response?.data?.message || "发送失败" }
}

async function handleLogin() {
  error.value = ""
  let result
  if (mode.value === "password") result = await auth.login(phone.value, password.value)
  else result = await auth.loginCode({ phone: phone.value, code: code.value })
  if (result.success) router.push(route.query.redirect || "/")
  else error.value = result.message
}
</script>

<style scoped>
.auth-page { min-height: 100vh; background: linear-gradient(135deg, var(--primary), var(--primary-light)); padding: 40px 24px; display: flex; flex-direction: column; }
.auth-header { text-align: center; color: #fff; margin-bottom: 32px; }
.auth-header h1 { font-size: 32px; margin-bottom: 8px; }
.auth-header p { font-size: 14px; opacity: 0.9; }
.auth-tabs { display: flex; background: rgba(255,255,255,0.2); border-radius: 10px; padding: 3px; margin-bottom: 24px; }
.auth-tabs button { flex: 1; padding: 10px; font-size: 15px; border-radius: 8px; color: rgba(255,255,255,0.8); font-weight: 500; }
.auth-tabs button.active { background: #fff; color: var(--primary); }
.auth-form { background: #fff; border-radius: var(--radius); padding: 24px; box-shadow: 0 8px 32px rgba(0,0,0,0.12); }
.auth-footer { text-align: center; margin-top: 20px; }
.auth-footer a { color: #fff; font-size: 14px; }
</style>
