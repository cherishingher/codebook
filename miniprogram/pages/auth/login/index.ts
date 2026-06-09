import { getApiBaseUrl, setApiBaseUrl } from '../../../services/api'
import { seedDemo } from '../../../services/demo'

Page({
  data: {
    apiBaseUrl: '',
    campusId: '',
    studentId: '',
    teacherId: ''
  },

  onLoad() {
    const role = getApp<IAppOption>().globalData.currentRole
    this.setData({
      apiBaseUrl: getApiBaseUrl(),
      campusId: role?.campusId ? String(role.campusId) : '',
      studentId: role?.studentId ? String(role.studentId) : '',
      teacherId: role?.teacherId ? String(role.teacherId) : ''
    })
  },

  onApiInput(event: { detail: { value: string } }) {
    this.setData({ apiBaseUrl: event.detail.value })
  },

  onCampusInput(event: { detail: { value: string } }) {
    this.setData({ campusId: event.detail.value })
  },

  onStudentInput(event: { detail: { value: string } }) {
    this.setData({ studentId: event.detail.value })
  },

  onTeacherInput(event: { detail: { value: string } }) {
    this.setData({ teacherId: event.detail.value })
  },

  async connectDemo() {
    const app = getApp<IAppOption>()
    setApiBaseUrl(this.data.apiBaseUrl)
    const state = await seedDemo()
    app.globalData.demoState = state
    app.globalData.currentRole = {
      role: 'learner',
      campusId: state.campus.id,
      studentId: state.student.id,
      teacherId: state.teacher.id
    }
    wx.setStorageSync('currentRole', app.globalData.currentRole)
    wx.showToast({ title: '连接成功', icon: 'success' })
    wx.navigateTo({ url: '/pages/auth/role-switch/index' })
  },

  enterLearner() {
    this.enterRole('learner')
  },

  enterTeacher() {
    this.enterRole('teacher')
  },

  enterCampus() {
    this.enterRole('campus_admin')
  },

  enterRole(role: string) {
    setApiBaseUrl(this.data.apiBaseUrl)
    const currentRole = {
      role,
      campusId: Number(this.data.campusId) || undefined,
      studentId: Number(this.data.studentId) || undefined,
      teacherId: Number(this.data.teacherId) || undefined
    }
    if (role === 'learner' && !currentRole.studentId) {
      wx.showToast({ title: '请填写学员ID', icon: 'none' })
      return
    }
    if (role === 'teacher' && !currentRole.teacherId) {
      wx.showToast({ title: '请填写老师ID', icon: 'none' })
      return
    }
    if (role === 'campus_admin' && !currentRole.campusId) {
      wx.showToast({ title: '请填写校区ID', icon: 'none' })
      return
    }
    const app = getApp<IAppOption>()
    app.globalData.currentRole = currentRole
    wx.setStorageSync('currentRole', currentRole)
    wx.showToast({ title: '身份已保存', icon: 'success' })
    if (role === 'learner') {
      wx.redirectTo({ url: '/pages/learner/home/index' })
    } else if (role === 'teacher') {
      wx.redirectTo({ url: '/pages/teacher/today/index' })
    } else {
      wx.redirectTo({ url: '/pages/campus/dashboard/index' })
    }
  },

  goRoleSwitch() {
    wx.navigateTo({ url: '/pages/auth/role-switch/index' })
  }
})
