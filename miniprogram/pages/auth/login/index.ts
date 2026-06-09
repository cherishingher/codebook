import { localLogin } from '../../../services/auth'
import { getApiBaseUrl, setApiBaseUrl, setToken } from '../../../services/api'

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

  enterLearner() {
    this.enterRole('learner')
  },

  enterTeacher() {
    this.enterRole('teacher')
  },

  enterCampus() {
    this.enterRole('campus_admin')
  },

  async enterRole(role: string) {
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
    const login = await localLogin({
      openid: `local:${role}:${currentRole.campusId || 0}:${currentRole.studentId || 0}:${currentRole.teacherId || 0}`,
      name: '本地调试用户',
      role,
      campus_id: currentRole.campusId,
      student_id: currentRole.studentId,
      teacher_id: currentRole.teacherId
    })
    setToken(login.token)
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
