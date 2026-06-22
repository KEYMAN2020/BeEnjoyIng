import axios from "axios"

const api = axios.create({
  baseURL: "/api/v1",
  timeout: 15000,
  headers: { "Content-Type": "application/json" }
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem("token")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
}, error => Promise.reject(error))

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token")
      const path = window.location.pathname
      if (path !== "/login" && path !== "/register") {
        window.location.href = `/login?redirect=${encodeURIComponent(path)}`
      }
    }
    return Promise.reject(error)
  }
)

export default api

export const authAPI = {
  login: d => api.post("/auth/login", d),
  register: d => api.post("/auth/register", d),
  sendCode: d => api.post("/auth/send-code", d),
  loginCode: d => api.post("/auth/login-code", d),
  refresh: d => api.post("/auth/refresh", d),
  logout: () => api.post("/auth/logout"),
  resetPassword: d => api.post("/auth/reset-password", d),
  changePassword: d => api.post("/auth/change-password", d),
  verifyIdentity: d => api.post("/auth/verify-identity", d)
}

export const activitiesAPI = {
  list: p => api.get("/activities", { params: p }),
  create: d => api.post("/activities", d),
  categories: () => api.get("/activities/categories"),
  tags: () => api.get("/activities/tags"),
  my: p => api.get("/activities/my", { params: p }),
  nearby: p => api.get("/activities/nearby", { params: p }),
  detail: id => api.get(`/activities/${id}`),
  update: (id, d) => api.put(`/activities/${id}`, d),
  delete: id => api.delete(`/activities/${id}`),
  disband: id => api.post(`/activities/${id}/disband`),
  complete: id => api.post(`/activities/${id}/complete`),
  signup: id => api.post(`/activities/${id}/signup`),
  cancel: id => api.post(`/activities/${id}/cancel`),
  signups: id => api.get(`/activities/${id}/signups`),
  checkin: id => api.post(`/activities/${id}/checkin`),
  favorite: id => api.post(`/activities/${id}/favorite`),
  unfavorite: id => api.delete(`/activities/${id}/favorite`),
  rate: (id, d) => api.post(`/activities/${id}/rate`, d),
  review: (id, d) => api.post(`/activities/${id}/review`, d),
  report: (id, d) => api.post(`/activities/${id}/report`, d),
  waitlist: id => api.post(`/activities/${id}/waitlist`),
  albums: id => api.get(`/activities/${id}/albums`),
  uploadPhoto: (id, d) => api.post(`/activities/${id}/albums`, d),
  deletePhoto: (aId, pId) => api.delete(`/activities/${aId}/albums/${pId}`),
  reportSummary: (id, d) => api.post(`/activities/${id}/report-summary`, d),
  sitePhotos: (id, d) => api.post(`/activities/${id}/site-photos`, d),
  myFavorites: p => api.get("/activities/my-favorites", { params: p }),
  searchPlaces: p => api.get("/activities/search-places", { params: p }),
  weather: id => api.get(`/activities/${id}/weather`)
}

export const usersAPI = {
  me: () => api.get("/users/me"),
  updateMe: d => api.put("/users/me", d),
  publicProfile: id => api.get(`/users/${id}/public`),
  userStats: id => api.get(`/users/${id}/stats`),
  search: p => api.get("/users/search", { params: p }),
  uploadAvatar: d => api.post("/users/upload-avatar", d),
  friendRequest: d => api.post("/users/friends/request", d),
  handleFriendRequest: (rid, d) => api.put(`/users/friends/request/${rid}`, d),
  friends: () => api.get("/users/friends"),
  pendingFriendRequests: () => api.get("/users/friends/requests/pending"),
  removeFriend: fid => api.delete(`/users/friends/${fid}`),
  messages: () => api.get("/users/messages"),
  sendMessage: d => api.post("/users/messages", d),
  messagesWith: uid => api.get(`/users/messages/with/${uid}`),
  reportUser: (tid, d) => api.post(`/users/${tid}/report`, d)
}

export const chatAPI = {
  groups: () => api.get("/chat/groups"),
  createGroup: d => api.post("/chat/groups", d),
  messages: (gid, p) => api.get(`/chat/groups/${gid}/messages`, { params: p }),
  sendMessage: (gid, d) => api.post(`/chat/groups/${gid}/messages`, d),
  readMessages: gid => api.post(`/chat/groups/${gid}/read`),
  leaveGroup: gid => api.delete(`/chat/groups/${gid}/leave`)
}

export const captainAPI = {
  apply: d => api.post("/captain/apply", d),
  application: () => api.get("/captain/application"),
  profile: () => api.get("/captain/profile"),
  updateProfile: d => api.put("/captain/profile", d),
  training: () => api.get("/captain/training"),
  submitTraining: d => api.post("/captain/training", d)
}

export const paymentAPI = {
  create: d => api.post("/payment/create", d),
  records: p => api.get("/payment/records", { params: p }),
  recordDetail: id => api.get(`/payment/records/${id}`),
  refund: id => api.post(`/payment/${id}/refund`),
  subscription: () => api.get("/payment/subscription"),
  createSubscription: d => api.post("/payment/subscription", d),
  cancelSubscription: () => api.post("/payment/subscription/cancel")
}

export const notificationAPI = {
  list: () => api.get("/notifications"),
  read: id => api.put(`/notifications/${id}/read`),
  readAll: () => api.post("/notifications/read-all")
}

export const partnerAPI = {
  streets: p => api.get("/partner/streets", { params: p }),
  profiles: p => api.get("/partner/profiles", { params: p }),
  userProfile: id => api.get(`/partner/profiles/${id}`),
  apply: d => api.post("/partner/apply", d)
}

export const healthAPI = {
  declare: d => api.post("/health/declare", d),
  insurance: aid => api.get(`/health/insurance/${aid}`)
}

export const systemAPI = {
  config: key => api.get(`/system/config/${key}`)
}

export const regionsAPI = {
  list: () => api.get("/regions")
}
