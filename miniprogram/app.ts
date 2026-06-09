App<IAppOption>({
  onLaunch() {
    const savedApiBaseUrl = wx.getStorageSync('apiBaseUrl')
    const savedRole = wx.getStorageSync('currentRole')
    if (savedApiBaseUrl) {
      this.globalData.apiBaseUrl = savedApiBaseUrl
    }
    if (savedRole) {
      this.globalData.currentRole = savedRole
    }
  },
  globalData: {
    apiBaseUrl: 'http://127.0.0.1:8000/api/v1',
    token: '',
    currentRole: null,
    demoState: null
  }
})
