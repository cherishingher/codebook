import { getDemoState } from '../../../services/demo'
import { getLearnerLessonDetail, getLearnerLessons } from '../../../services/learner'
import { attendanceText, deductionText } from '../../../utils/format'

type LessonItem = { id: number; title: string; status: string; start_time: string }

Page({
  data: {
    isRealMode: false,
    studentName: '',
    courseName: '',
    lessons: [] as Array<Record<string, unknown>>
  },

  onShow() {
    this.load()
  },

  async load() {
    const role = getApp<IAppOption>().globalData.currentRole
    if (role?.studentId) {
      try {
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
        return
      } catch (error) {
        wx.showToast({ title: '真实课表读取失败，显示演示数据', icon: 'none' })
      }
    }
    const state = await getDemoState()
    this.setData({
      isRealMode: false,
      studentName: state.student.name,
      courseName: state.course.name,
      lessons: state.lesson_students.map((item) => ({
        ...item,
        title: state.course.name,
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
