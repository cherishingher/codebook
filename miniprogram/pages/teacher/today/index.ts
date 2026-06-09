import { createDemoLesson, getDemoState } from '../../../services/demo'
import { attendanceText, deductionText } from '../../../utils/format'

Page({
  data: {
    campusName: '',
    teacherName: '',
    studentName: '',
    courseName: '',
    lessons: [] as Array<Record<string, unknown>>
  },

  onShow() {
    this.load()
  },

  async load() {
    const state = await getDemoState()
    getApp<IAppOption>().globalData.demoState = state
    this.setData({
      campusName: state.campus.name,
      teacherName: state.teacher.name,
      studentName: state.student.name,
      courseName: state.course.name,
      lessons: state.lesson_students.map((item) => ({
        ...item,
        attendanceText: attendanceText(item.attendance_status),
        deductionText: deductionText(item.deduction_status),
        tagClass: item.attendance_status === 'present' || item.attendance_status === 'late'
          ? 'ok'
          : item.attendance_status === 'absent'
            ? 'bad'
            : 'warn'
      }))
    })
  },

  async createLesson() {
    await createDemoLesson()
    wx.showToast({ title: '已新建课次', icon: 'success' })
    this.load()
  },

  goDetail(event: WechatMiniprogram.TouchEvent) {
    const lessonId = event.currentTarget.dataset.lessonId
    wx.navigateTo({ url: `/pages/teacher/lesson-detail/index?lessonId=${lessonId}` })
  },

  switchRole() {
    wx.redirectTo({ url: '/pages/auth/role-switch/index' })
  }
})
