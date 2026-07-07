// uni-app API layer
const B = 'http://124.220.16.67:5000/api/v1'

function request(method, path, data) {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync('token') || ''
    uni.request({
      url: B + path, method: method, data: data,
      header: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
      success: function(res) {
        if (res.statusCode === 200 && res.data.code === 0) resolve(res.data)
        else reject(new Error(res.data.message || 'request failed'))
      },
      fail: reject
    })
  })
}

export const api = {
  get: function(p) { return request('GET', p) },
  post: function(p, d) { return request('POST', p, d) },
  put: function(p, d) { return request('PUT', p, d) },
  delete: function(p) { return request('DELETE', p) },
}

export const activitiesAPI = {
  list: function(params) { return api.get('/activities?' + new URLSearchParams(params).toString()) },
  detail: function(id) { return api.get('/activities/' + id) },
  create: function(data) { return api.post('/activities', data) },
  signup: function(id) { return api.post('/activities/' + id + '/signup') },
  cancel: function(id) { return api.post('/activities/' + id + '/cancel') },
  disband: function(id) { return api.post('/activities/' + id + '/disband') },
  complete: function(id) { return api.post('/activities/' + id + '/complete') },
  categories: function() { return api.get('/activities/categories') },
  my: function(params) { return api.get('/activities/my?' + new URLSearchParams(params).toString()) },
  signups: function(id) { return api.get('/activities/' + id + '/signups') },
}

export const authAPI = {
  login: function(data) { return api.post('/auth/login', data) },
  register: function(data) { return api.post('/auth/register', data) },
  sendCode: function(phone) { return api.post('/auth/send-code', { phone: phone }) },
}

export const chatAPI = {
  groups: function() { return api.get('/chat/groups') },
  messages: function(id, params) { return api.get('/chat/groups/' + id + '/messages?' + new URLSearchParams(params).toString()) },
  send: function(id, data) { return api.post('/chat/groups/' + id + '/messages', data) },
  leave: function(id) { return api.delete('/chat/groups/' + id + '/leave') },
}

export const userAPI = {
  me: function() { return api.get('/users/me') },
  update: function(data) { return api.put('/users/me', data) },
  uploadAvatar: function(fp) {
    return new Promise(function(resolve, reject) {
      uni.uploadFile({
        url: B + '/users/me/avatar', filePath: fp, name: 'file',
        header: { 'Authorization': 'Bearer ' + (uni.getStorageSync('token') || '') },
        success: function(res) { resolve(JSON.parse(res.data)) },
        fail: reject
      })
    })
  },
  profile: function(id) { return api.get('/users/' + id) },
  search: function(k) { return api.get('/users/search?keyword=' + encodeURIComponent(k)) },
  friends: function() { return api.get('/users/friends') },
  addFriend: function(id) { return api.post('/users/friends', { friend_id: id }) },
  deleteFriend: function(id) { return api.delete('/users/friends/' + id) },
}

export const usersAPI = {
  messages: function() { return api.get('/users/messages') },
  pendingFriendRequests: function() { return api.get('/users/friend-requests') },
  messagesWith: function(id) { return api.get('/users/messages/' + id) },
  sendMessage: function(id, data) { return api.post('/users/messages/' + id, data) },
  search: function(k) { return api.get('/users/search?keyword=' + encodeURIComponent(k)) },
  friends: userAPI.friends,
  addFriend: userAPI.addFriend,
  profile: userAPI.profile,
}

export const geoAPI = {
  search: function(keyword, city) { return api.get('/geo/search?keyword=' + encodeURIComponent(keyword) + '&city=' + encodeURIComponent(city || '')) },
}
