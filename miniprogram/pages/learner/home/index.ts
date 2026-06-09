import { getDemoState } from '../../../services/demo'
import { attendanceText, deductionText, formatHours } from '../../../utils/format'

Page({
  data: {
    studentName: '',
    campusName: '',
    courseName: '',
    balanceText: '0.00课时',
    latestAttendance: '待确认',
    lessons: [] as Array<Record<string, unknown>>
  },

  onShow() {
    this.load()
  },

  async load() {
    const state = await getDemoState()
    getApp<IAppOption>().globalData.demoState = state
    const latest = state.lesson_students[0]
    this.setData({
      studentName: state.student.name,
      campusName: state.campus.name,
      courseName: state.course.name,
      balanceText: formatHours(Number(state.account.balance_hours)),
      latestAttendance: latest ? attendanceText(latest.attendance_status) : '暂无',
      lessons: state.lesson_students.map((item) => ({
        ...item,
        attendanceText: attendanceText(item.attendance_status),
        deductionText: deductionText(item.deduction_status)
      }))
    })
  },

  goSchedule() {
    wx.navigateTo({ url: '/pages/learner/schedule/index' })
  },
  goHours() {
    wx.navigateTo({ url: '/pages/learner/hours/index' })
  },
  switchRole() {
    wx.redirectTo({ url: '/pages/auth/role-switch/index' })
  }
})
