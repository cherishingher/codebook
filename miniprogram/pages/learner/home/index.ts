import { getDemoState } from '../../../services/demo'
import { getLearnerDashboard, getLearnerLessons } from '../../../services/learner'
import { attendanceText, deductionText, formatHours } from '../../../utils/format'

type LearnerDashboard = {
  student: { id: number; name: string }
  today_lessons: Array<{ id: number; title: string; status: string }>
  hour_summary: Array<{ balance_hours: number }>
}

Page({
  data: {
    isRealMode: false,
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
    const role = getApp<IAppOption>().globalData.currentRole
    if (role?.studentId) {
      try {
        const [dashboard, lessonsRes] = await Promise.all([
          getLearnerDashboard(role.studentId) as Promise<LearnerDashboard>,
          getLearnerLessons(role.studentId) as Promise<{ items: Array<{ id: number; title: string; status: string }> }>
        ])
        const totalBalance = dashboard.hour_summary
          .reduce((sum, item) => sum + Number(item.balance_hours), 0)
        this.setData({
          isRealMode: true,
          studentName: dashboard.student.name,
          campusName: role.campusId ? `校区 #${role.campusId}` : '已绑定学员',
          courseName: '全部课程',
          balanceText: formatHours(totalBalance),
          latestAttendance: lessonsRes.items[0]?.status || '暂无',
          lessons: lessonsRes.items.slice(0, 5).map((item) => ({
            id: item.id,
            lesson_id: item.id,
            title: item.title,
            attendanceText: item.status,
            deductionText: '查看课表详情',
            deducted_hours: 0
          }))
        })
        return
      } catch (error) {
        wx.showToast({ title: '真实学员数据读取失败，显示演示数据', icon: 'none' })
      }
    }
    const state = await getDemoState()
    getApp<IAppOption>().globalData.demoState = state
    const latest = state.lesson_students[0]
    this.setData({
      isRealMode: false,
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
