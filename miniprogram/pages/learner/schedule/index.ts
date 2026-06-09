import { getLearnerLessonDetail, getLearnerLessons } from '../../../services/learner'
import { attendanceText, deductionText } from '../../../utils/format'

type LessonItem = { id: number; title: string; status: string; start_time: string }

Page({
  data: {
    isRealMode: true,
    studentName: '',
    courseName: '',
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
    const lessonsRes = await getLearnerLessons(role.studentId) as { items: LessonItem[] }
    const details = await Promise.all(
      lessonsRes.items.slice(0, 20).map((item) => getLearnerLessonDetail(role.studentId as number, item.id)
        .catch(() => null))
    ) as Array<null | {
      lesson: { id: number; title: string; start_time: string }
      lesson_student: {
        attendance_status: string
        deduction_status: string
        deducted_hours: number
        note?: string
      }
      attendance?: { source: string }
    }>
    this.setData({
      isRealMode: true,
      studentName: `学员 #${role.studentId}`,
      courseName: '全部课程',
      lessons: details.filter((item) => item !== null).map((detail) => {
        const item = detail as NonNullable<typeof detail>
        const status = item.lesson_student.attendance_status
        return {
          id: item.lesson.id,
          lesson_id: item.lesson.id,
          title: item.lesson.title,
          attendanceText: attendanceText(status),
          deductionText: deductionText(item.lesson_student.deduction_status),
          deducted_hours: item.lesson_student.deducted_hours,
          note: item.lesson_student.note,
          tagClass: status === 'present' || status === 'late'
            ? 'ok'
            : status === 'absent'
              ? 'bad'
              : 'warn'
        }
      })
    })
  }
})
