import axios from 'axios'
const api = axios.create({ baseURL: '/api/v1' })
api.interceptors.request.use(c => { const t = localStorage.getItem('token'); if(t) c.headers.Authorization = 'Bearer '+t; return c })
export const authAPI = { login: d => api.post('/auth/login',d), loginCode: d => api.post('/auth/login-code',d), register: d => api.post('/auth/register',d), sendCode: d => api.post('/auth/send-code',d), changePassword: d => api.post('/auth/change-password',d) }
export const usersAPI = { me: () => api.get('/users/me'), publicProfile: id => api.get('/users/'+id+'/public'), userStats: id => api.get('/users/'+id+'/stats'), friends: () => api.get('/users/friends'), messages: () => api.get('/users/messages'), pendingFriendRequests: () => api.get('/users/friend-requests/pending'), removeFriend: id => api.delete('/users/friends/'+id), updateProfile: d => api.put('/users/profile',d) }
export const activitiesAPI = { list: p => api.get('/activities',{params:p}), create: d => api.post('/activities',d), nearby: p => api.get('/activities/nearby',{params:p}), categories: () => api.get('/activities/categories'), tags: () => api.get('/activities/tags'), my: p => api.get('/activities/my',{params:p}), myFavorites: () => api.get('/activities/favorites') }
export const chatAPI = { groups: () => api.get('/chat/groups') }
export default api
