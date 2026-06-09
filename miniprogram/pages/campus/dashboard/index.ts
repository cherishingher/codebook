import { getCampusDashboard, runAbsenceJob } from '../../../services/campus'
import { formatHours } from '../../../utils/format'

type CampusDashboard = {
  today_lessons: number
  expected_attendances: number
  present_count: number
  late_count: number
  absent_count: number
  deducted_hours: number
  pending_exceptions: number
  devices_online: number
}

Page({
  data: {
    isRealMode: false,
    campusName: '',
    deviceName: '',
    deviceStatus: '',
    balanceText: '0.00课时',
    todayLessons: 0,
    expectedAttendances: 0,
    presentCount: 0,
    lateCount: 0,
    absentCount: 0,
    deductedHours: '0.00课时',
    devicesOnline: 0
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
    const dashboard = await getCampusDashboard(role.campusId) as CampusDashboard
    this.setData({
      isRealMode: true,
      campusName: `校区 #${role.campusId}`,
      deviceName: '本地设备',
      deviceStatus: dashboard.devices_online > 0 ? '在线' : '待连接',
      balanceText: `${dashboard.expected_attendances} 人次`,
      todayLessons: dashboard.today_lessons,
      expectedAttendances: dashboard.expected_attendances,
      presentCount: dashboard.present_count,
      lateCount: dashboard.late_count,
      absentCount: dashboard.absent_count,
      deductedHours: formatHours(Number(dashboard.deducted_hours || 0)),
      devicesOnline: dashboard.devices_online
    })
  },

  async newLesson() {
    wx.navigateTo({ url: '/pages/campus/lessons/index?action=new' })
  },

  async punch() {
    wx.showToast({ title: '真实打卡由 Mac 摄像头完成', icon: 'none' })
  },

  async runAbsence() {
    const result = await runAbsenceJob()
    wx.showToast({ title: `生成缺勤 ${result.created} 条`, icon: 'none' })
    this.load()
  },

  goStudents() {
    wx.navigateTo({ url: '/pages/campus/students/index' })
  },
  goLessons() {
    wx.navigateTo({ url: '/pages/campus/lessons/index' })
  },
  switchRole() {
    wx.redirectTo({ url: '/pages/auth/role-switch/index' })
  }
})
