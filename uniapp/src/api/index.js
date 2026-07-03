// ── API 层 (uni.request 替代 axios) ──
const BASE = 'http://124.220.16.67:5000/api/v1'

function request(method, path, data = null) {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync('token') || ''
    uni.request({
      url: BASE + path, method, data,
      header: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
      success: (res) => {
        if (res.data.code === 0) resolve(res.data)
        else reject(new Error(res.data.message || '请求失败'))
      },
      fail: (err) => reject(err)
    })
  })
}

export const api = {
  get: (path) => request('GET', path),
  post: (path, data) => request('POST', path, data),
  put: (path, data) => request('PUT', path, data),
  delete: (path) => request('DELETE', path),
}

export const activitiesAPI = {
  list: (params) => api.get('/activities?' + new URLSearchParams(params).toString()),
  detail: (id) => api.get('/activities/' + id),
  create: (data) => api.post('/activities', data),
  signup: (id) => api.post('/activities/' + id + '/signup'),
  cancel: (id) => api.post('/activities/' + id + '/cancel'),
  disband: (id) => api.post('/activities/' + id + '/disband'),
  complete: (id) => api.post('/activities/' + id + '/complete'),
  categories: () => api.get('/activities/categories'),
  my: (params) => api.get('/activities/my?' + new URLSearchParams(params).toString()),
  signups: (id) => api.get('/activities/' + id + '/signups'),
}

export const chatAPI = {
  groups: () => api.get('/chat/groups'),
  messages: (id, params) => api.get('/chat/groups/' + id + '/messages?' + new URLSearchParams(params).toString()),
  send: (id, data) => api.post('/chat/groups/' + id + '/messages', data),
  leave: (id) => api.delete('/chat/groups/' + id + '/leave'),
}

export const userAPI = {
  me: () => api.get('/users/me'),
  update: (data) => api.put('/users/me', data),
  friends: () => api.get('/users/friends'),
  deleteFriend: (id) => api.delete('/users/friends/' + id),
}

export const geoAPI = {
  search: (keyword, city) => api.get('/geo/search?keyword=' + encodeURIComponent(keyword) + '&city=' + encodeURIComponent(city || '')),
}

export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  sendCode: (phone) => api.post('/auth/send-code', { phone })
}

export const usersAPI = {
  me: () => api.get('/users/me'),
  update: (data) => api.put('/users/me', data),
  uploadAvatar: (filePath) => new Promise((resolve, reject) => {
    uni.uploadFile({
      url: 'http://124.220.16.67:5000/api/v1/users/me/avatar',
      filePath, name: 'file',
      header: { 'Authorization': 'Bearer ' + (uni.getStorageSync('token') || '') },
      success: res => resolve(JSON.parse(res.data)),
      fail: reject
    })
  }),
  profile: (id) => api.get('/users/' + id),
  addFriend: (id) => api.post('/users/friends', { friend_id: id }),
  friends: () => api.get('/users/friends'),
  deleteFriend: (id) => api.delete('/users/friends/' + id),
  search: (keyword) => api.get('/users/search?keyword=' + encodeURIComponent(keyword)),
  locations: () => api.get('/users/locations')
}
