type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  data?: Record<string, unknown>
}

export function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const app = getApp<IAppOption>()
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.apiBaseUrl}${path}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        Authorization: app.globalData.token ? `Bearer ${app.globalData.token}` : ''
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          reject(res)
        }
      },
      fail: reject
    })
  })
}

