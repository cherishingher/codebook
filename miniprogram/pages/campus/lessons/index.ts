import { createDemoLesson, getDemoState, runAbsenceDemo } from '../../../services/demo'
import { attendanceText, deductionText } from '../../../utils/format'

Page({
  data: {
    campusName: '',
    courseName: '',
    studentName: '',
    lessons: [] as Array<Record<string, unknown>>
  },

  onShow() {
    this.load()
  },

  async load() {
    const state = await getDemoState()
    this.setData({
      campusName: state.campus.name,
      courseName: state.course.name,
      studentName: state.student.name,
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

  async newLesson() {
    await createDemoLesson()
    wx.showToast({ title: '已新建课次', icon: 'success' })
    this.load()
  },

  async runAbsence() {
    const result = await runAbsenceDemo()
    wx.showToast({ title: `生成缺勤 ${result.created} 条`, icon: 'none' })
    this.load()
  }
})
