App<IAppOption>({
  onLaunch() {
    const savedApiBaseUrl = wx.getStorageSync('apiBaseUrl')
    const savedRole = wx.getStorageSync('currentRole')
    const savedToken = wx.getStorageSync('token')
    if (savedApiBaseUrl) {
      this.globalData.apiBaseUrl = savedApiBaseUrl
    }
    if (savedRole) {
      this.globalData.currentRole = savedRole
    }
    if (savedToken) {
      this.globalData.token = savedToken
    }
  },
  globalData: {
    apiBaseUrl: 'http://127.0.0.1:8000/api/v1',
    token: '',
    currentRole: null
  }
})
