import { confirmAttendance, getTeacherLessonDetail } from '../../../services/teacher'
import { attendanceText, deductionText } from '../../../utils/format'

type LessonStudentView = {
  id: number
  student_id: number
  studentName: string
  attendance_status: string
  deduction_status: string
  attendanceText: string
  deductionText: string
  tagClass: string
}

Page({
  data: {
    isRealMode: true,
    lessonId: 0,
    teacherId: 0,
    studentId: 0,
    studentName: '',
    courseName: '',
    attendanceText: '待确认',
    deductionText: '待处理',
    students: [] as LessonStudentView[]
  },

  onLoad(options: Record<string, string>) {
    this.setData({ lessonId: Number(options.lessonId || 0) })
  },

  onShow() {
    this.load()
  },

  async load() {
    const role = getApp<IAppOption>().globalData.currentRole
    if (!role?.teacherId || !this.data.lessonId) {
      wx.showToast({ title: '缺少老师身份或课次ID', icon: 'none' })
      return
    }
    const detail = await getTeacherLessonDetail(role.teacherId, this.data.lessonId) as {
      course?: { name: string }
      students: Array<{
        id: number
        student_id: number
        attendance_status: string
        deduction_status: string
        student?: { name: string }
      }>
    }
    const students = detail.students.map((item) => this.mapStudent(item))
    const selected = students.find((item) => item.student_id === this.data.studentId) || students[0]
    this.setData({
      isRealMode: true,
      teacherId: role.teacherId,
      courseName: detail.course?.name || '课次详情',
      students,
      studentId: selected?.student_id || 0,
      studentName: selected?.studentName || '',
      attendanceText: selected?.attendanceText || '待确认',
      deductionText: selected?.deductionText || '待处理'
    })
  },

  mapStudent(item: {
    id: number
    student_id: number
    attendance_status: string
    deduction_status: string
    student?: { name: string }
  }): LessonStudentView {
    return {
      id: item.id,
      student_id: item.student_id,
      studentName: item.student?.name || `学员 #${item.student_id}`,
      attendance_status: item.attendance_status,
      deduction_status: item.deduction_status,
      attendanceText: attendanceText(item.attendance_status),
      deductionText: deductionText(item.deduction_status),
      tagClass: item.attendance_status === 'present' || item.attendance_status === 'late'
        ? 'ok'
        : item.attendance_status === 'absent'
          ? 'bad'
          : 'warn'
    }
  },

  selectStudent(event: WechatMiniprogram.TouchEvent) {
    const studentId = Number(event.currentTarget.dataset.studentId)
    const selected = this.data.students.find((item) => item.student_id === studentId)
    if (!selected) {
      return
    }
    this.setData({
      studentId: selected.student_id,
      studentName: selected.studentName,
      attendanceText: selected.attendanceText,
      deductionText: selected.deductionText
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
      teacherId: this.data.teacherId || undefined,
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
