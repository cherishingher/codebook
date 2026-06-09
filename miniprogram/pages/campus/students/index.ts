import {
  addCampusHourLedger,
  createCampusHourAccount,
  createCampusStudent,
  getCampusCourses,
  getCampusHourAccounts,
  getCampusHourLedgers,
  getCampusStudents
} from '../../../services/campus'
import { formatHours, ledgerText, signedHours } from '../../../utils/format'

type ListResponse<T> = { items: T[] }
type StudentItem = { id: number; name: string; student_no?: string; phone?: string; status?: string }
type CourseItem = { id: number; name: string }
type AccountItem = { id: number; course_id: number; balance_hours: number; status: string }
type LedgerItem = {
  id: number
  change_type: string
  change_hours: number
  balance_before: number
  balance_after: number
  source: string
  reason?: string
}

Page({
  data: {
    isRealMode: true,
    campusId: 0,
    keyword: '',
    studentName: '',
    studentNo: '',
    studentPhone: '',
    courseName: '',
    campusName: '',
    balanceText: '0.00课时',
    students: [] as StudentItem[],
    courses: [] as CourseItem[],
    accounts: [] as AccountItem[],
    ledgers: [] as Array<Record<string, unknown>>,
    selectedStudentId: 0,
    selectedStudentName: '',
    courseNames: [] as string[],
    courseIndex: 0,
    addHours: '10',
    addReason: '手动加课'
  },

  onShow() {
    this.load()
  },

  async load() {
    const role = getApp<IAppOption>().globalData.currentRole
    if (!role?.campusId) {
      wx.showToast({ title: '请先登录校区身份', icon: 'none' })
      return
    }
    const [studentsRes, coursesRes] = await Promise.all([
      getCampusStudents(role.campusId, this.data.keyword) as Promise<ListResponse<StudentItem>>,
      getCampusCourses(role.campusId) as Promise<ListResponse<CourseItem>>
    ])
    const selected = studentsRes.items.find((item) => item.id === this.data.selectedStudentId)
      || studentsRes.items[0]
    this.setData({
      isRealMode: true,
      campusId: role.campusId,
      campusName: `校区 #${role.campusId}`,
      students: studentsRes.items,
      courses: coursesRes.items,
      courseNames: coursesRes.items.map((item) => `${item.id} · ${item.name}`),
      selectedStudentId: selected?.id || 0,
      selectedStudentName: selected?.name || '',
      studentName: '',
      studentNo: '',
      studentPhone: ''
    })
    if (selected) {
      await this.loadStudentFinance(selected.id)
    } else {
      this.setData({ accounts: [], ledgers: [], balanceText: '暂无学员' })
    }
  },

  async loadStudentFinance(studentId: number) {
    const [accountsRes, ledgersRes] = await Promise.all([
      getCampusHourAccounts(this.data.campusId, studentId) as Promise<ListResponse<AccountItem>>,
      getCampusHourLedgers(this.data.campusId, studentId) as Promise<ListResponse<LedgerItem>>
    ])
    const account = accountsRes.items[0]
    const course = this.data.courses.find((item) => item.id === account?.course_id)
    this.setData({
      accounts: accountsRes.items,
      courseName: course?.name || '',
      balanceText: account ? formatHours(Number(account.balance_hours)) : '未开课时账户',
      ledgers: ledgersRes.items.map((item) => ({
        ...item,
        typeText: ledgerText(item.change_type),
        changeText: signedHours(Number(item.change_hours))
      }))
    })
  },

  onKeywordInput(event: { detail: { value: string } }) {
    this.setData({ keyword: event.detail.value })
  },

  onNameInput(event: { detail: { value: string } }) {
    this.setData({ studentName: event.detail.value })
  },

  onNoInput(event: { detail: { value: string } }) {
    this.setData({ studentNo: event.detail.value })
  },

  onPhoneInput(event: { detail: { value: string } }) {
    this.setData({ studentPhone: event.detail.value })
  },

  onCourseChange(event: { detail: { value: string } }) {
    this.setData({ courseIndex: Number(event.detail.value) })
  },

  onHoursInput(event: { detail: { value: string } }) {
    this.setData({ addHours: event.detail.value })
  },

  onReasonInput(event: { detail: { value: string } }) {
    this.setData({ addReason: event.detail.value })
  },

  async search() {
    await this.load()
  },

  async createStudent() {
    if (!this.data.studentName.trim()) {
      wx.showToast({ title: '请输入学员姓名', icon: 'none' })
      return
    }
    await createCampusStudent({
      campus_id: this.data.campusId,
      name: this.data.studentName,
      student_no: this.data.studentNo || undefined,
      phone: this.data.studentPhone || undefined
    })
    wx.showToast({ title: '学员已创建', icon: 'success' })
    this.load()
  },

  async selectStudent(event: WechatMiniprogram.TouchEvent) {
    const studentId = Number(event.currentTarget.dataset.studentId)
    const student = this.data.students.find((item) => item.id === studentId)
    this.setData({
      selectedStudentId: studentId,
      selectedStudentName: student?.name || ''
    })
    await this.loadStudentFinance(studentId)
  },

  async addHoursToSelected() {
    if (!this.data.selectedStudentId) {
      wx.showToast({ title: '请先选择学员', icon: 'none' })
      return
    }
    const course = this.data.courses[this.data.courseIndex]
    if (!course) {
      wx.showToast({ title: '请先创建课程', icon: 'none' })
      return
    }
    const account = this.data.accounts.find((item) => item.course_id === course.id)
    if (account) {
      await addCampusHourLedger(account.id, this.data.addHours, this.data.addReason)
    } else {
      await createCampusHourAccount({
        campus_id: this.data.campusId,
        student_id: this.data.selectedStudentId,
        course_id: course.id,
        initial_hours: this.data.addHours,
        reason: this.data.addReason
      })
    }
    wx.showToast({ title: '课时已更新', icon: 'success' })
    await this.loadStudentFinance(this.data.selectedStudentId)
  }
})
