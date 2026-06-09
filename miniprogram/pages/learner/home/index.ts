import { getLearnerDashboard, getLearnerLessons } from '../../../services/learner'
import { formatHours } from '../../../utils/format'

type LearnerDashboard = {
  student: { id: number; name: string }
  today_lessons: Array<{ id: number; title: string; status: string }>
  hour_summary: Array<{ balance_hours: number }>
}

Page({
  data: {
    isRealMode: true,
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
    if (!role?.studentId) {
      wx.showToast({ title: '请先登录学员身份', icon: 'none' })
      return
    }
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
