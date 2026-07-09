import { createRouter, createWebHistory } from "vue-router"

const routes = [
  { path: "/", name: "Home", component: () => import("../views/Home.vue") },
  { path: "/login", name: "Login", component: () => import("../views/Login.vue") },
  { path: "/register", name: "Register", component: () => import("../views/Register.vue") },
  { path: "/messages", name: "Messages", component: () => import("../views/Messages.vue") },
  { path: "/messages/:groupId", name: "Chat", component: () => import("../views/Chat.vue") },
  { path: "/chat/private/:id", name: "PrivateChat", component: () => import("../views/PrivateChat.vue") },
  { path: "/groups", name: "GroupList", component: () => import("../views/GroupList.vue") },
  { path: "/contacts", name: "Contacts", component: () => import("../views/Contacts.vue") },
  { path: "/contacts/requests", name: "FriendRequests", component: () => import("../views/FriendRequests.vue") },
  { path: "/mine", name: "Mine", component: () => import("../views/Mine.vue") },
  { path: "/create", name: "CreateActivity", component: () => import("../views/CreateActivity.vue") },
  { path: "/edit/:id", name: "EditActivity", component: () => import("../views/EditActivity.vue") },
  { path: "/activity/:id", name: "ActivityDetail", component: () => import("../views/ActivityDetail.vue") },
  { path: "/activity/:id/signups", name: "ActivitySignups", component: () => import("../views/ActivitySignups.vue") },
  { path: "/profile/:id", name: "UserProfile", component: () => import("../views/UserProfile.vue") },
  { path: "/profile/edit", name: "ProfileEdit", component: () => import("../views/ProfileEdit.vue") },
  { path: "/:pathMatch(.*)*", redirect: "/" }
]

const router = createRouter({
  history: createWebHistory("/app/"),
  routes,
})

export default router
