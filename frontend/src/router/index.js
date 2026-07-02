import { createRouter, createWebHistory } from "vue-router"

const routes = [
  { path: "/", name: "Home", component: () => import("@/views/Home.vue"), meta: { title: "发现" } },
  { path: "/login", name: "Login", component: () => import("@/views/Login.vue"), meta: { guest: true } },
  { path: "/register", name: "Register", component: () => import("@/views/Register.vue"), meta: { guest: true } },
  { path: "/messages", name: "Messages", component: () => import("@/views/Messages.vue"), meta: { requiresAuth: true } },
  { path: "/messages/:groupId", name: "Chat", component: () => import("@/views/Chat.vue"), meta: { requiresAuth: true } },
  { path: "/chat/private/:id", name: "PrivateChat", component: () => import("@/views/PrivateChat.vue"), meta: { requiresAuth: true } },
  { path: "/groups", name: "GroupList", component: () => import("@/views/GroupList.vue"), meta: { requiresAuth: true } },
  { path: "/contacts", name: "Contacts", component: () => import("@/views/Contacts.vue"), meta: { requiresAuth: true } },
  { path: "/contacts/requests", name: "FriendRequests", component: () => import("@/views/FriendRequests.vue"), meta: { requiresAuth: true } },
  { path: "/mine", name: "Mine", component: () => import("@/views/Mine.vue"), meta: { requiresAuth: true } },
  { path: "/activity/:id", name: "ActivityDetail", component: () => import("@/views/ActivityDetail.vue") },
  { path: "/activity/:id/signups", name: "ActivitySignups", component: () => import("@/views/ActivitySignups.vue"), meta: { requiresAuth: true } },
  { path: "/create", name: "CreateActivity", component: () => import("@/views/CreateActivity.vue"), meta: { requiresAuth: true } },
  { path: "/edit/:id", name: "EditActivity", component: () => import("@/views/EditActivity.vue"), meta: { requiresAuth: true } },
  { path: "/profile/:id", name: "UserProfile", component: () => import("@/views/UserProfile.vue") },
  { path: "/profile/edit", name: "ProfileEdit", component: () => import("@/views/ProfileEdit.vue"), meta: { requiresAuth: true } },
  { path: "/:pathMatch(.*)*", redirect: "/" }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() { return { top: 0 } }
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} — 银发活力` : "银发活力 — BeEnjoyIng"
  const token = localStorage.getItem("token")
  if (to.meta.requiresAuth && !token) next({ name: "Login", query: { redirect: to.fullPath } })
  else if (to.meta.guest && token) next({ name: "Home" })
  else next()
})

export default router
