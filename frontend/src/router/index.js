import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue') },
  { path: '/messages', name: 'Messages', component: () => import('../views/Messages.vue') },
  { path: '/create', name: 'CreateActivity', component: () => import('../views/CreateActivity.vue') },
  { path: '/contacts', name: 'Contacts', component: () => import('../views/Contacts.vue') },
  { path: '/mine', name: 'Mine', component: () => import('../views/Mine.vue') },
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue') },
  { path: '/profile/:id', name: 'UserProfile', component: () => import('../views/UserProfile.vue') },
  { path: '/activity/:id', name: 'ActivityDetail', component: () => import('../views/ActivityDetail.vue') },
  { path: '/profile/edit', name: 'ProfileEdit', component: () => import('../views/ProfileEdit.vue') },
]

const router = createRouter({
  history: createWebHistory('/app/'),
  routes,
})

export default router
