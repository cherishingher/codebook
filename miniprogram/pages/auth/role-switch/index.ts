Page({
  goLearner() {
    wx.redirectTo({ url: '/pages/learner/home/index' })
  },
  goTeacher() {
    wx.redirectTo({ url: '/pages/teacher/today/index' })
  },
  goCampus() {
    wx.redirectTo({ url: '/pages/campus/dashboard/index' })
  }
})

