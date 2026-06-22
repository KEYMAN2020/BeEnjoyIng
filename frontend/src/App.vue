<template>
  <div id="app-root">
    <router-view />
    <nav class="bottom-nav" v-if="showNav">
      <router-link to="/">
        <span class="nav-icon">🏠</span>
        <span class="nav-label">发现</span>
      </router-link>
      <router-link to="/messages">
        <span class="nav-icon">💬</span>
        <span class="nav-label">消息</span>
      </router-link>
      <router-link to="/create" class="nav-create">
        <span class="nav-icon-create">➕</span>
        <span class="nav-label">发起</span>
      </router-link>
      <router-link to="/contacts">
        <span class="nav-icon">📋</span>
        <span class="nav-label">通讯录</span>
      </router-link>
      <router-link to="/mine">
        <span class="nav-icon">👤</span>
        <span class="nav-label">我的</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { computed } from "vue"
import { useRoute } from "vue-router"

const route = useRoute()

// 一级页面（显示底部导航栏）
const showNav = computed(() => {
  const topLevelPages = ["Home", "Messages", "Contacts", "Mine"]
  return topLevelPages.includes(route.name)
})
</script>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  background: #fff;
  border-top: 1.5px solid #E8E2DA;
  display: flex;
  justify-content: space-around;
  align-items: stretch;
  padding: 6px 0 env(safe-area-inset-bottom, 6px);
  z-index: 200;
  box-shadow: 0 -2px 16px rgba(0,0,0,0.09);
}

.bottom-nav a {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  flex: 1;
  padding: 6px 4px 4px;
  color: #999;
  border-radius: 0;
  transition: color 0.2s;
  text-decoration: none;
}

.bottom-nav a.router-link-active {
  color: #FF6B35;
}

.nav-icon {
  font-size: 26px;
  line-height: 1.1;
  display: block;
}

.nav-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.3px;
  line-height: 1;
}

/* 发起按钮特殊样式 */
.nav-create {
  position: relative;
}

.nav-icon-create {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  background: linear-gradient(135deg, #FF6B35, #E55A2B);
  border-radius: 50%;
  color: #fff;
  font-size: 24px;
  margin-top: -14px;
  box-shadow: 0 4px 16px rgba(255,107,53,0.45);
  transition: transform 0.15s;
}

.nav-create:active .nav-icon-create {
  transform: scale(0.92);
}
</style>
