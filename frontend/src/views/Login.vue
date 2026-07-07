<template>
  <div class="login-page">
    <!-- ═══ State bar ═══ -->
    <div class="login-statebar">9:41</div>

    <!-- ═══ Logo ═══ -->
    <div class="login-logo-area">
      <div class="login-logo">
        <svg width="48" height="48" viewBox="0 0 72 72"><circle fill="#06D6A0" transform="matrix(1 0 0 1 24 10)" cx="12" cy="12" r="12"/><path fill="#06D6A0" transform="matrix(1 0 0 1 16 31)" d="M0.4223 7.8406Q-0.5 10.3083 -0.5 13L0.5 13Q0.5 10.489 1.359 8.1907Q2.2015 5.9364 3.7476 4.2084Q5.3155 2.4561 7.3817 1.5007Q9.546 0.5 12 0.5L28 0.5Q30.4539 0.5 32.6183 1.5007Q34.6845 2.4561 36.2524 4.2084Q37.7985 5.9364 38.641 8.1907Q39.5 10.489 39.5 13L40.5 13Q40.5 10.3082 39.5777 7.8406Q38.6693 5.41 36.9976 3.5416Q35.2919 1.6352 33.038 0.593Q30.6739 -0.5 28 -0.5L12 -0.5Q9.326 -0.5 6.962 0.593Q4.7081 1.6352 3.0024 3.5416Q1.3307 5.41 0.4223 7.8406Z" fill-rule="evenodd"/></svg>
      </div>
      <div class="login-brand">银发圈</div>
      <div class="login-sub">中老年智慧养老服务平台</div>
    </div>

    <!-- ═══ Form ═══ -->
    <div class="login-form">
      <!-- Phone -->
      <div class="login-input-wrap">
        <span class="login-prefix">+86</span>
        <span class="login-divider">|</span>
        <input v-model="phone" type="tel" maxlength="11" placeholder="请输入手机号" />
      </div>

      <!-- Code mode -->
      <div v-if="mode==='code'" class="login-input-wrap" style="padding-right:8px">
        <input v-model="code" type="text" maxlength="6" placeholder="验证码" style="flex:1" />
        <button class="login-code-btn" @click="sendCode" :disabled="countdown>0">
          {{ countdown>0 ? countdown+'s' : '获取验证码' }}
        </button>
      </div>

      <!-- Password mode -->
      <div v-else class="login-input-wrap">
        <input v-model="password" type="password" placeholder="请输入密码" />
      </div>

      <!-- Error -->
      <div v-if="error" class="login-error">{{ error }}</div>

      <!-- Submit -->
      <button class="login-submit" @click="handleLogin" :disabled="auth.loading">
        {{ auth.loading ? '登录中...' : '登  录' }}
      </button>

      <!-- Switch mode -->
      <div class="login-switch">
        <span @click="mode = mode==='password' ? 'code' : 'password'">
          {{ mode==='password' ? '验证码登录' : '密码登录' }}
        </span>
      </div>

      <!-- Agreement -->
      <div class="login-agree">登录即同意《用户协议》和《隐私政策》</div>
    </div>

    <!-- ═══ Other login methods ═══ -->
    <div class="login-other">
      <div class="login-other-text"><span>— 其他登录方式 —</span></div>
      <div class="login-other-icons">
        <div class="login-oi">微</div>
        <div class="login-oi">支</div>
        <div class="login-oi">信</div>
      </div>
    </div>

    <!-- Register link -->
    <div class="login-reg">
      <router-link to="/register">还没有账号？立即注册</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authAPI } from '@/api'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const mode = ref('code')
const phone = ref('')
const password = ref('')
const code = ref('')
const error = ref('')
const countdown = ref(0)

async function sendCode() {
  if (!phone.value || phone.value.length < 11) { error.value = '请输入正确的手机号'; return }
  try {
    await authAPI.sendCode({ phone: phone.value })
    countdown.value = 60
    const timer = setInterval(() => { countdown.value--; if (countdown.value <= 0) clearInterval(timer) }, 1000)
    error.value = ''
  } catch (e) { error.value = e.response?.data?.message || '发送失败' }
}

async function handleLogin() {
  error.value = ''
  let result
  if (mode.value === 'password') result = await auth.login(phone.value, password.value)
  else result = await auth.loginCode({ phone: phone.value, code: code.value })
  if (result.success) router.push(route.query.redirect || '/')
  else error.value = result.message
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #06D6A0 0%, #0096C7 100%);
  display: flex; flex-direction: column;
  padding: 60px 28px 40px;
  font-family: 'PingFang SC', sans-serif;
}

/* State bar */
.login-statebar { color: #fff; font-size: 15px; font-weight: 600; margin-bottom: 20px }

/* Logo */
.login-logo-area { text-align: center; margin-bottom: 36px; margin-top: 10px }
.login-logo { width: 96px; height: 96px; border-radius: 50%; background: #fff; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; box-shadow: 0 4px 16px rgba(0,0,0,.1) }
.login-brand { color: #fff; font-size: 28px; font-weight: 700; margin-bottom: 6px }
.login-sub { color: #7DE8D0; font-size: 14px }

/* Form */
.login-form { display: flex; flex-direction: column; gap: 14px }

.login-input-wrap {
  display: flex; align-items: center;
  height: 52px; background: #4DD4B8; border-radius: 26px;
  padding: 0 18px; gap: 8px;
}
.login-prefix { color: #fff; font-size: 16px; font-weight: 600 }
.login-divider { color: rgba(255,255,255,.4); font-size: 16px }
.login-input-wrap input {
  flex: 1; height: 100%; border: none; outline: none; background: transparent;
  color: #fff; font-size: 16px;
}
.login-input-wrap input::placeholder { color: #7DE8D0 }

.login-code-btn {
  background: #fff; color: #06D6A0; border: none;
  padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 600;
  cursor: pointer; white-space: nowrap;
}
.login-code-btn:disabled { opacity: .6 }

.login-error { color: #fff; font-size: 13px; text-align: center; background: rgba(255,0,0,.2); padding: 8px; border-radius: 8px }

.login-submit {
  height: 52px; background: #fff; color: #06D6A0;
  border: none; border-radius: 26px; font-size: 18px; font-weight: 700;
  cursor: pointer; margin-top: 4px;
}
.login-submit:active { opacity: .85 }
.login-submit:disabled { opacity: .6 }

.login-switch { text-align: center }
.login-switch span { color: #C8F7E8; font-size: 14px; cursor: pointer }
.login-agree { text-align: center; color: #7DE8D0; font-size: 12px; margin-top: 4px }

/* Other login */
.login-other { margin-top: auto; text-align: center }
.login-other-text { margin-bottom: 16px }
.login-other-text span { color: #7DE8D0; font-size: 13px; padding: 0 12px }
.login-other-icons { display: flex; justify-content: center; gap: 24px }
.login-oi { width: 44px; height: 44px; border-radius: 50%; background: #4DD4B8; display: flex; align-items: center; justify-content: center; font-size: 16px; color: #fff; font-weight: 600 }

/* Register */
.login-reg { text-align: center; margin-top: 24px }
.login-reg a { color: #C8F7E8; font-size: 14px; text-decoration: none }
</style>
