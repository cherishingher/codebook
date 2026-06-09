import { getCampusCourses, getCampusStudents } from '../../../services/campus'
import { createDemoLesson, getDemoState } from '../../../services/demo'
import { createTeacherLesson, getTeacherLessons } from '../../../services/teacher'
import { attendanceText, deductionText } from '../../../utils/format'

type ListResponse<T> = { items: T[] }
type BasicItem = { id: number; name: string }
type LessonItem = { id: number; title: string; start_time: string; end_time: string; status: string; campus_id: number; course_id: number }

Page({
  data: {
    isRealMode: false,
    campusId: 0,
    teacherId: 0,
    campusName: '',
    teacherName: '',
    studentName: '',
    courseName: '',
    lessons: [] as Array<Record<string, unknown>>,
    courses: [] as BasicItem[],
    students: [] as BasicItem[],
    courseNames: [] as string[],
    studentNames: [] as string[],
    courseIndex: 0,
    studentIndex: 0,
    titleInput: '老师新建课次'
  },

  onShow() {
    this.load()
  },

  async load() {
    const role = getApp<IAppOption>().globalData.currentRole
    if (role?.teacherId) {
      try {
        const lessonRes = await getTeacherLessons(role.teacherId) as ListResponse<LessonItem>
        const campusId = role.campusId || lessonRes.items[0]?.campus_id || 0
        let courses: BasicItem[] = []
        let students: BasicItem[] = []
        if (campusId) {
          const [courseRes, studentRes] = await Promise.all([
            getCampusCourses(campusId) as Promise<ListResponse<BasicItem>>,
            getCampusStudents(campusId) as Promise<ListResponse<BasicItem>>
          ])
          courses = courseRes.items
          students = studentRes.items
        }
        this.setData({
          isRealMode: true,
          campusId,
          teacherId: role.teacherId,
          campusName: campusId ? `校区 #${campusId}` : '未绑定校区',
          teacherName: `老师 #${role.teacherId}`,
          studentName: students[0]?.name || '',
          courseName: courses[0]?.name || '',
          courses,
          students,
          courseNames: courses.map((item) => `${item.id} · ${item.name}`),
          studentNames: students.map((item) => `${item.id} · ${item.name}`),
          lessons: lessonRes.items.map((item) => ({
            id: item.id,
            lesson_id: item.id,
            title: item.title,
            attendanceText: item.status,
            deductionText: item.start_time,
            tagClass: item.status === 'cancelled' ? 'bad' : 'ok',
            deducted_hours: 0
          }))
        })
        return
      } catch (error) {
        wx.showToast({ title: '真实课次读取失败，显示演示数据', icon: 'none' })
      }
    }
    const state = await getDemoState()
    getApp<IAppOption>().globalData.demoState = state
    this.setData({
      isRealMode: false,
      campusName: state.campus.name,
      teacherName: state.teacher.name,
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
  },

  onCourseChange(event: { detail: { value: string } }) {
    this.setData({ courseIndex: Number(event.detail.value) })
  },

  onStudentChange(event: { detail: { value: string } }) {
    this.setData({ studentIndex: Number(event.detail.value) })
  },

  onTitleInput(event: { detail: { value: string } }) {
    this.setData({ titleInput: event.detail.value })
  },

  async createLesson() {
    if (this.data.isRealMode) {
      const course = this.data.courses[this.data.courseIndex]
      const student = this.data.students[this.data.studentIndex]
      if (!this.data.campusId || !course || !student) {
        wx.showToast({ title: '请先绑定校区并创建课程/学员', icon: 'none' })
        return
      }
      const now = new Date()
      await createTeacherLesson({
        campus_id: this.data.campusId,
        course_id: course.id,
        teacher_id: this.data.teacherId,
        title: this.data.titleInput || course.name,
        classroom_name: 'A101',
        start_time: new Date(now.getTime() + 5 * 60 * 1000).toISOString(),
        end_time: new Date(now.getTime() + 95 * 60 * 1000).toISOString(),
        checkin_start_time: new Date(now.getTime() - 10 * 60 * 1000).toISOString(),
        checkin_end_time: new Date(now.getTime() + 30 * 60 * 1000).toISOString(),
        late_after_time: new Date(now.getTime() + 10 * 60 * 1000).toISOString(),
        default_hour_cost: '1.00',
        student_ids: [student.id]
      })
      wx.showToast({ title: '已新建真实课次', icon: 'success' })
      this.load()
      return
    }
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
