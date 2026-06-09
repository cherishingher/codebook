import { getDemoState } from '../../../services/demo'

Page({
  data: {
    campusName: ''
  },

  async onShow() {
    const app = getApp<IAppOption>()
    const role = app.globalData.currentRole
    if (role?.campusId || role?.studentId || role?.teacherId) {
      this.setData({ campusName: role.campusId ? `校区 #${role.campusId}` : '已保存真实身份' })
      return
    }
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
    const savedRole = getApp<IAppOption>().globalData.currentRole
    const currentRole = {
      role,
      campusId: state?.campus.id || savedRole?.campusId,
      studentId: state?.student.id || savedRole?.studentId,
      teacherId: state?.teacher.id || savedRole?.teacherId
    }
    if (role === 'learner' && !currentRole.studentId) {
      wx.showToast({ title: '请先填写学员ID', icon: 'none' })
      return false
    }
    if (role === 'teacher' && !currentRole.teacherId) {
      wx.showToast({ title: '请先填写老师ID', icon: 'none' })
      return false
    }
    if (role === 'campus_admin' && !currentRole.campusId) {
      wx.showToast({ title: '请先填写校区ID', icon: 'none' })
      return false
    }
    getApp<IAppOption>().globalData.currentRole = currentRole
    wx.setStorageSync('currentRole', currentRole)
    return true
  },

  goLearner() {
    if (!this.setRole('learner')) return
    wx.redirectTo({ url: '/pages/learner/home/index' })
  },
  goTeacher() {
    if (!this.setRole('teacher')) return
    wx.redirectTo({ url: '/pages/teacher/today/index' })
  },
  goCampus() {
    if (!this.setRole('campus_admin')) return
    wx.redirectTo({ url: '/pages/campus/dashboard/index' })
  },
  goLogin() {
    wx.redirectTo({ url: '/pages/auth/login/index' })
  }
})
