import {
  createCampusLesson,
  getCampusCourses,
  getCampusLessons,
  getCampusStudents,
  getCampusTeachers,
  getDeductionRules,
  runAbsenceJob,
  upsertDeductionRule
} from '../../../services/campus'
import { createDemoLesson, getDemoState, runAbsenceDemo } from '../../../services/demo'
import { attendanceText, deductionText } from '../../../utils/format'

type ListResponse<T> = { items: T[] }
type BasicItem = { id: number; name: string; title?: string; student_no?: string }
type LessonItem = { id: number; title: string; start_time: string; end_time: string; status: string }

Page({
  data: {
    isRealMode: false,
    campusId: 0,
    campusName: '',
    courseName: '',
    studentName: '',
    lessons: [] as Array<Record<string, unknown>>,
    courses: [] as BasicItem[],
    teachers: [] as BasicItem[],
    students: [] as BasicItem[],
    courseNames: [] as string[],
    teacherNames: [] as string[],
    studentNames: [] as string[],
    courseIndex: 0,
    teacherIndex: 0,
    studentIndex: 0,
    titleInput: '临时课次',
    classroomInput: 'A101',
    ruleText: '到课/迟到扣课，缺勤待处理，请假不扣课'
  },

  onShow() {
    this.load()
  },

  async load() {
    const role = getApp<IAppOption>().globalData.currentRole
    if (role?.campusId) {
      try {
        const [lessonsRes, coursesRes, teachersRes, studentsRes, rulesRes] = await Promise.all([
          getCampusLessons(role.campusId) as Promise<ListResponse<LessonItem>>,
          getCampusCourses(role.campusId) as Promise<ListResponse<BasicItem>>,
          getCampusTeachers(role.campusId) as Promise<ListResponse<BasicItem>>,
          getCampusStudents(role.campusId) as Promise<ListResponse<BasicItem>>,
          getDeductionRules(role.campusId) as Promise<ListResponse<Record<string, string>>>
        ])
        const rules = rulesRes.items[0]
        this.setData({
          isRealMode: true,
          campusId: role.campusId,
          campusName: `校区 #${role.campusId}`,
          courseName: coursesRes.items[0]?.name || '暂无课程',
          studentName: studentsRes.items[0]?.name || '暂无学员',
          lessons: lessonsRes.items.map((item) => ({
            id: item.id,
            lesson_id: item.id,
            title: item.title,
            attendanceText: item.status,
            deductionText: item.start_time,
            tagClass: item.status === 'cancelled' ? 'bad' : 'ok',
            deducted_hours: 0
          })),
          courses: coursesRes.items,
          teachers: teachersRes.items,
          students: studentsRes.items,
          courseNames: coursesRes.items.map((item) => `${item.id} · ${item.name}`),
          teacherNames: teachersRes.items.map((item) => `${item.id} · ${item.name}`),
          studentNames: studentsRes.items.map((item) => `${item.id} · ${item.name}`),
          ruleText: rules
            ? `到课:${rules.present_action} 迟到:${rules.late_action} 缺勤:${rules.absent_action} 请假:${rules.leave_action}`
            : '未设置规则'
        })
        return
      } catch (error) {
        wx.showToast({ title: '真实课次读取失败，显示演示数据', icon: 'none' })
      }
    }
    const state = await getDemoState()
    this.setData({
      isRealMode: false,
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

  onCourseChange(event: { detail: { value: string } }) {
    this.setData({ courseIndex: Number(event.detail.value) })
  },

  onTeacherChange(event: { detail: { value: string } }) {
    this.setData({ teacherIndex: Number(event.detail.value) })
  },

  onStudentChange(event: { detail: { value: string } }) {
    this.setData({ studentIndex: Number(event.detail.value) })
  },

  onTitleInput(event: { detail: { value: string } }) {
    this.setData({ titleInput: event.detail.value })
  },

  onClassroomInput(event: { detail: { value: string } }) {
    this.setData({ classroomInput: event.detail.value })
  },

  async newLesson() {
    if (this.data.isRealMode) {
      const course = this.data.courses[this.data.courseIndex]
      const teacher = this.data.teachers[this.data.teacherIndex]
      const student = this.data.students[this.data.studentIndex]
      if (!course || !teacher || !student) {
        wx.showToast({ title: '请先创建课程、老师和学员', icon: 'none' })
        return
      }
      const now = new Date()
      const start = new Date(now.getTime() + 5 * 60 * 1000)
      const end = new Date(now.getTime() + 95 * 60 * 1000)
      const checkinStart = new Date(now.getTime() - 10 * 60 * 1000)
      const checkinEnd = new Date(now.getTime() + 30 * 60 * 1000)
      const lateAfter = new Date(now.getTime() + 10 * 60 * 1000)
      await createCampusLesson({
        campus_id: this.data.campusId,
        course_id: course.id,
        teacher_id: teacher.id,
        title: this.data.titleInput || course.name,
        classroom_name: this.data.classroomInput,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        checkin_start_time: checkinStart.toISOString(),
        checkin_end_time: checkinEnd.toISOString(),
        late_after_time: lateAfter.toISOString(),
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

  async saveDefaultRule() {
    if (!this.data.isRealMode) {
      wx.showToast({ title: '演示模式无需保存规则', icon: 'none' })
      return
    }
    await upsertDeductionRule({
      campus_id: this.data.campusId,
      scope_type: 'campus',
      present_action: 'deduct',
      late_action: 'deduct',
      absent_action: 'manual_required',
      leave_action: 'not_deduct',
      exception_action: 'manual_required'
    })
    wx.showToast({ title: '规则已保存', icon: 'success' })
    this.load()
  },

  async runAbsence() {
    if (this.data.isRealMode) {
      const result = await runAbsenceJob()
      wx.showToast({ title: `生成缺勤 ${result.created} 条`, icon: 'none' })
      this.load()
      return
    }
    const result = await runAbsenceDemo()
    wx.showToast({ title: `生成缺勤 ${result.created} 条`, icon: 'none' })
    this.load()
  }
})
