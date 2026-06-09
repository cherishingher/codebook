import { getApiBaseUrl, setApiBaseUrl } from '../../../services/api'
import { seedDemo } from '../../../services/demo'

Page({
  data: {
    apiBaseUrl: ''
  },

  onLoad() {
    this.setData({ apiBaseUrl: getApiBaseUrl() })
  },

  onApiInput(event: WechatMiniprogram.Input) {
    this.setData({ apiBaseUrl: event.detail.value })
  },

  async connectDemo() {
    const app = getApp<IAppOption>()
    setApiBaseUrl(this.data.apiBaseUrl)
    const state = await seedDemo()
    app.globalData.demoState = state
    app.globalData.currentRole = {
      role: 'learner',
      campusId: state.campus.id,
      studentId: state.student.id,
      teacherId: state.teacher.id
    }
    wx.setStorageSync('currentRole', app.globalData.currentRole)
    wx.showToast({ title: '连接成功', icon: 'success' })
    wx.navigateTo({ url: '/pages/auth/role-switch/index' })
  },

  goRoleSwitch() {
    wx.navigateTo({ url: '/pages/auth/role-switch/index' })
  }
})
