<template>
  <div class="reg-page">
    <div class="reg-statebar">9:41</div>

    <!-- Logo -->
    <div class="reg-logo-area">
      <div class="reg-logo">
        <svg width="48" height="48" viewBox="0 0 72 72"><circle fill="#06D6A0" transform="matrix(1 0 0 1 24 10)" cx="12" cy="12" r="12"/><path fill="#06D6A0" transform="matrix(1 0 0 1 16 31)" d="M0.4223 7.8406Q-0.5 10.3083 -0.5 13L0.5 13Q0.5 10.489 1.359 8.1907Q2.2015 5.9364 3.7476 4.2084Q5.3155 2.4561 7.3817 1.5007Q9.546 0.5 12 0.5L28 0.5Q30.4539 0.5 32.6183 1.5007Q34.6845 2.4561 36.2524 4.2084Q37.7985 5.9364 38.641 8.1907Q39.5 10.489 39.5 13L40.5 13Q40.5 10.3082 39.5777 7.8406Q38.6693 5.41 36.9976 3.5416Q35.2919 1.6352 33.038 0.593Q30.6739 -0.5 28 -0.5L12 -0.5Q9.326 -0.5 6.962 0.593Q4.7081 1.6352 3.0024 3.5416Q1.3307 5.41 0.4223 7.8406Z" fill-rule="evenodd"/></svg>
      </div>
      <div class="reg-brand">银发圈</div>
      <div class="reg-sub">注册账号，加入活动</div>
    </div>

    <!-- Form -->
    <div class="reg-form">
      <div class="reg-input-wrap">
        <span class="reg-prefix">+86</span>
        <span class="reg-divider">|</span>
        <input v-model="phone" type="tel" maxlength="11" placeholder="请输入手机号" />
      </div>

      <div class="reg-input-wrap" style="padding-right:8px">
        <input v-model="code" type="text" maxlength="6" placeholder="验证码" style="flex:1" />
        <button class="reg-code-btn" @click="sendCode" :disabled="countdown>0">
          {{ countdown>0 ? countdown+'s' : '获取验证码' }}
        </button>
      </div>

      <div class="reg-input-wrap">
        <input v-model="password" type="password" placeholder="请设置密码（至少6位）" />
      </div>

      <div class="reg-input-wrap">
        <input v-model="nickname" type="text" placeholder="给自己取个昵称" />
      </div>

      <div v-if="error" class="reg-error">{{ error }}</div>

      <button class="reg-submit" @click="handleRegister" :disabled="auth.loading">
        {{ auth.loading ? '注册中...' : '注  册' }}
      </button>
    </div>

    <div class="reg-footer">
      <router-link to="/login">已有账号？去登录</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authAPI } from '@/api'

const router = useRouter()
const auth = useAuthStore()
const phone = ref('')
const code = ref('')
const password = ref('')
const nickname = ref('')
const error = ref('')
const countdown = ref(0)

async function sendCode() {
  if (!phone.value || phone.value.length < 11) { error.value = '请输入正确的手机号'; return }
  try {
    await authAPI.sendCode({ phone: phone.value })
    countdown.value = 60
    const t = setInterval(() => { countdown.value--; if (countdown.value <= 0) clearInterval(t) }, 1000)
    error.value = ''
  } catch (e) { error.value = e.response?.data?.message || '发送失败' }
}

async function handleRegister() {
  error.value = ''
  const result = await auth.register({ phone: phone.value, code: code.value, password: password.value, nickname: nickname.value })
  if (result.success) router.push('/login')
  else error.value = result.message
}
</script>

<style scoped>
.reg-page { min-height: 100vh; background: linear-gradient(180deg, #06D6A0 0%, #0096C7 100%); display: flex; flex-direction: column; padding: 60px 28px 40px; font-family: 'PingFang SC', sans-serif }
.reg-statebar { color: #fff; font-size: 15px; font-weight: 600; margin-bottom: 20px }
.reg-logo-area { text-align: center; margin-bottom: 32px; margin-top: 10px }
.reg-logo { width: 96px; height: 96px; border-radius: 50%; background: #fff; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; box-shadow: 0 4px 16px rgba(0,0,0,.1) }
.reg-brand { color: #fff; font-size: 28px; font-weight: 700; margin-bottom: 6px }
.reg-sub { color: #7DE8D0; font-size: 14px }
.reg-form { display: flex; flex-direction: column; gap: 14px }
.reg-input-wrap { display: flex; align-items: center; height: 52px; background: #4DD4B8; border-radius: 26px; padding: 0 18px; gap: 8px }
.reg-prefix { color: #fff; font-size: 16px; font-weight: 600 }
.reg-divider { color: rgba(255,255,255,.4); font-size: 16px }
.reg-input-wrap input { flex: 1; height: 100%; border: none; outline: none; background: transparent; color: #fff; font-size: 16px }
.reg-input-wrap input::placeholder { color: #7DE8D0 }
.reg-code-btn { background: #fff; color: #06D6A0; border: none; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 600; cursor: pointer; white-space: nowrap }
.reg-code-btn:disabled { opacity: .6 }
.reg-error { color: #fff; font-size: 13px; text-align: center; background: rgba(255,0,0,.2); padding: 8px; border-radius: 8px }
.reg-submit { height: 52px; background: #fff; color: #06D6A0; border: none; border-radius: 26px; font-size: 18px; font-weight: 700; cursor: pointer; margin-top: 4px }
.reg-submit:active { opacity: .85 }
.reg-submit:disabled { opacity: .6 }
.reg-footer { text-align: center; margin-top: 24px }
.reg-footer a { color: #C8F7E8; font-size: 14px; text-decoration: none }
</style>
