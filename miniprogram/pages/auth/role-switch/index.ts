Page({
  data: {
    campusName: ''
  },

  onShow() {
    const role = getApp<IAppOption>().globalData.currentRole
    this.setData({ campusName: role?.campusId ? `校区 #${role.campusId}` : '请先在登录页填写身份 ID' })
  },

  setRole(role: string) {
    const savedRole = getApp<IAppOption>().globalData.currentRole
    const currentRole = {
      role,
      campusId: savedRole?.campusId,
      studentId: savedRole?.studentId,
      teacherId: savedRole?.teacherId
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
