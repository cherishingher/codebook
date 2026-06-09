import { getDemoState } from '../../../services/demo'
import { attendanceText, deductionText } from '../../../utils/format'

Page({
  data: {
    studentName: '',
    courseName: '',
    lessons: [] as Array<Record<string, unknown>>
  },

  onShow() {
    this.load()
  },

  async load() {
    const state = await getDemoState()
    this.setData({
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
  }
})
