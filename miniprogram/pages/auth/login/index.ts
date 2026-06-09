import { loginWithCode } from '../../../services/auth'

Page({
  async login() {
    const app = getApp<IAppOption>()
    wx.login({
      success: async ({ code }) => {
        const result = await loginWithCode(code)
        app.globalData.token = result.token
        wx.navigateTo({ url: '/pages/auth/role-switch/index' })
      }
    })
  }
})

