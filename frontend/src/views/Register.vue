<template>
  <div class="auth-page">
    <div class="auth-header">
      <h1>🏕️ 银发活力</h1>
      <p>注册账号，加入活动</p>
    </div>

    <form class="auth-form" @submit.prevent="handleRegister">
      <div class="form-group">
        <label>手机号</label>
        <input v-model="phone" type="tel" maxlength="11" placeholder="请输入手机号" />
      </div>

      <div class="form-group">
        <label>验证码</label>
        <div style="display:flex;gap:8px">
          <input v-model="code" type="text" maxlength="6" placeholder="请输入验证码" style="flex:1" />
          <button type="button" class="btn btn-outline btn-sm" @click="sendCode" :disabled="countdown > 0" style="white-space:nowrap">
            {{ countdown > 0 ? `${countdown}s` : "获取验证码" }}
          </button>
        </div>
      </div>

      <div class="form-group">
        <label>密码</label>
        <input v-model="password" type="password" placeholder="请设置密码（至少6位）" />
      </div>

      <div class="form-group">
        <label>昵称</label>
        <input v-model="nickname" type="text" placeholder="给自己取个昵称" />
      </div>

      <div class="form-error" v-if="error">{{ error }}</div>

      <button type="submit" class="btn btn-primary btn-block" :disabled="auth.loading" style="margin-top:16px">
        {{ auth.loading ? "注册中..." : "注册" }}
      </button>
    </form>

    <div class="auth-footer">
      <router-link to="/login">已有账号？去登录</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { authAPI } from "@/api"

const router = useRouter()
const auth = useAuthStore()
const phone = ref("")
const code = ref("")
const password = ref("")
const nickname = ref("")
const error = ref("")
const countdown = ref(0)

async function sendCode() {
  if (!phone.value || phone.value.length < 11) { error.value = "请输入正确的手机号"; return }
  try {
    await authAPI.sendCode({ phone: phone.value })
    countdown.value = 60
    const t = setInterval(() => { countdown.value--; if (countdown.value <= 0) clearInterval(t) }, 1000)
    error.value = ""
  } catch (e) { error.value = e.response?.data?.message || "发送失败" }
}

async function handleRegister() {
  error.value = ""
  const result = await auth.register({ phone: phone.value, code: code.value, password: password.value, nickname: nickname.value })
  if (result.success) router.push("/login")
  else error.value = result.message
}
</script>

<style scoped>
.auth-page { min-height: 100vh; background: linear-gradient(135deg, var(--primary), var(--primary-light)); padding: 40px 24px; display: flex; flex-direction: column; }
.auth-header { text-align: center; color: #fff; margin-bottom: 32px; }
.auth-header h1 { font-size: 32px; margin-bottom: 8px; }
.auth-header p { font-size: 14px; opacity: 0.9; }
.auth-form { background: #fff; border-radius: var(--radius); padding: 24px; box-shadow: 0 8px 32px rgba(0,0,0,0.12); }
.auth-footer { text-align: center; margin-top: 20px; }
.auth-footer a { color: #fff; font-size: 14px; }
</style>