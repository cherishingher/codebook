import { getDemoState } from '../../../services/demo'

Page({
  data: {
    campusName: ''
  },

  async onShow() {
    const app = getApp<IAppOption>()
    try {
      const state = await getDemoState()
      app.globalData.demoState = state
      this.setData({ campusName: state.campus.name })
    } catch (error) {
      this.setData({ campusName: app.globalData.demoState?.campus.name || '' })
    }
  },

  setRole(role: string) {
    const state = getApp<IAppOption>().globalData.demoState
    const currentRole = {
      role,
      campusId: state?.campus.id,
      studentId: state?.student.id,
      teacherId: state?.teacher.id
    }
    getApp<IAppOption>().globalData.currentRole = currentRole
    wx.setStorageSync('currentRole', currentRole)
  },

  goLearner() {
    this.setRole('learner')
    wx.redirectTo({ url: '/pages/learner/home/index' })
  },
  goTeacher() {
    this.setRole('teacher')
    wx.redirectTo({ url: '/pages/teacher/today/index' })
  },
  goCampus() {
    this.setRole('campus_admin')
    wx.redirectTo({ url: '/pages/campus/dashboard/index' })
  },
  goLogin() {
    wx.redirectTo({ url: '/pages/auth/login/index' })
  }
})
