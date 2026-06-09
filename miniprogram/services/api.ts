type RequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: Record<string, unknown>
  loadingText?: string
}

export function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const app = getApp<IAppOption>()
  if (options.loadingText) {
    wx.showLoading({ title: options.loadingText, mask: true })
  }
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.apiBaseUrl}${path}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        Authorization: app.globalData.token ? `Bearer ${app.globalData.token}` : '',
        'content-type': 'application/json'
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          wx.showToast({ title: `请求失败 ${res.statusCode}`, icon: 'none' })
          reject(res)
        }
      },
      fail: (err) => {
        wx.showToast({ title: '无法连接后端服务', icon: 'none' })
        reject(err)
      },
      complete: () => {
        if (options.loadingText) {
          wx.hideLoading()
        }
      }
    })
  })
}

export function setApiBaseUrl(url: string) {
  const app = getApp<IAppOption>()
  const normalized = url.replace(/\/$/, '')
  app.globalData.apiBaseUrl = normalized
  wx.setStorageSync('apiBaseUrl', normalized)
}

export function getApiBaseUrl() {
  return getApp<IAppOption>().globalData.apiBaseUrl
}

export function setToken(token: string) {
  const app = getApp<IAppOption>()
  app.globalData.token = token
  wx.setStorageSync('token', token)
}

export function clearToken() {
  const app = getApp<IAppOption>()
  app.globalData.token = ''
  wx.removeStorageSync('token')
}
