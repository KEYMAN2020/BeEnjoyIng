const B='http://124.220.16.67:5000/api/v1'

export function request(o){
  o = o || {}
  const t=uni.getStorageSync('token')
  return new Promise((rv,rj)=>{
    uni.request({
      url:B+o.url,
      method:o.method||'GET',
      data:o.data,
      header:{'Content-Type':'application/json',...(t?{Authorization:'Bearer '+t}:{})},
      success(r){
        if(r.statusCode>=200&&r.statusCode<300)rv(r.data)
        else rj(r.data||{code:r.statusCode,message:'fail'})
      },
      fail(e){rj(e)}
    })
  })
}

export function hasToken(){return !!uni.getStorageSync('token')}

export function doLogin(onSuccess){
  uni.login({
    provider:'weixin',
    success(loginRes){
      const code=loginRes.code
      if(!code){uni.showToast({title:'登录取消',icon:'none'});return}
      uni.showLoading({title:'登录中'})
      request({url:'/auth/wx-login',method:'POST',data:{code}}).then(r=>{
        uni.hideLoading()
        if(r&&r.code===0){
          uni.setStorageSync('token',r.data.access_token)
          uni.showToast({title:'登录成功',icon:'none'})
          if(onSuccess)setTimeout(onSuccess,400)
        }else{
          uni.showToast({title:r.message||'登录失败',icon:'none'})
        }
      }).catch(()=>{uni.hideLoading();uni.showToast({title:'网络错误',icon:'none'})})
    },
    fail(err){
      uni.showToast({title:'请先登录微信开发者工具',icon:'none',duration:3000})
    }
  })
}
