import { getDemoState } from '../../../services/demo'
import { confirmAttendance } from '../../../services/teacher'
import { attendanceText, deductionText } from '../../../utils/format'

Page({
  data: {
    lessonId: 0,
    studentId: 0,
    studentName: '',
    courseName: '',
    attendanceText: '待确认',
    deductionText: '待处理'
  },

  onLoad(options: Record<string, string>) {
    this.setData({ lessonId: Number(options.lessonId || 0) })
  },

  onShow() {
    this.load()
  },

  async load() {
    const state = await getDemoState()
    const selected = state.lesson_students.find((item) => item.lesson_id === this.data.lessonId)
      || state.lesson_students[0]
    this.setData({
      lessonId: selected?.lesson_id || 0,
      studentId: state.student.id,
      studentName: state.student.name,
      courseName: state.course.name,
      attendanceText: selected ? attendanceText(selected.attendance_status) : '待确认',
      deductionText: selected ? deductionText(selected.deduction_status) : '待处理'
    })
  },

  async submit(attendanceStatus: string, deductionAction: string, reason: string) {
    if (!this.data.lessonId || !this.data.studentId) {
      wx.showToast({ title: '没有可确认的课次', icon: 'none' })
      return
    }
    await confirmAttendance({
      lessonId: this.data.lessonId,
      studentId: this.data.studentId,
      attendanceStatus,
      deductionAction,
      reason
    })
    wx.showToast({ title: '已确认', icon: 'success' })
    this.load()
  },

  confirmPresent() {
    this.submit('present', 'deduct', '教师确认到课')
  },

  confirmLate() {
    this.submit('late', 'deduct', '教师确认迟到')
  },

  confirmAbsent() {
    this.submit('absent', 'manual_required', '教师确认缺勤')
  },

  confirmLeave() {
    this.submit('leave', 'not_deduct', '教师确认请假')
  },

  back() {
    wx.navigateBack()
  }
})
