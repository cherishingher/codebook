import { getCampusDashboard, runAbsenceJob } from '../../../services/campus'
import { createDemoLesson, getDemoState, punchDemo, runAbsenceDemo, seedDemo } from '../../../services/demo'
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
    if (role?.campusId) {
      try {
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
        return
      } catch (error) {
        wx.showToast({ title: '真实看板读取失败，显示演示数据', icon: 'none' })
      }
    }
    const state = await getDemoState().catch(() => seedDemo())
    getApp<IAppOption>().globalData.demoState = state
    this.setData({
      isRealMode: false,
      campusName: state.campus.name,
      deviceName: state.device.name,
      deviceStatus: state.device.status === 'active' ? '在线' : state.device.status,
      balanceText: formatHours(Number(state.account.balance_hours)),
      todayLessons: state.lesson_students.length,
      expectedAttendances: state.lesson_students.length,
      presentCount: state.lesson_students.filter((item) => ['present', 'late'].includes(item.attendance_status)).length,
      lateCount: state.lesson_students.filter((item) => item.attendance_status === 'late').length,
      absentCount: state.lesson_students.filter((item) => item.attendance_status === 'absent').length,
      deductedHours: formatHours(Math.abs(state.ledgers
        .filter((item) => item.change_type === 'deduct')
        .reduce((sum, item) => sum + Number(item.change_hours), 0))),
      devicesOnline: state.device.status === 'active' ? 1 : 0
    })
  },

  async newLesson() {
    if (this.data.isRealMode) {
      wx.navigateTo({ url: '/pages/campus/lessons/index?action=new' })
      return
    }
    await createDemoLesson()
    wx.showToast({ title: '已新建课次', icon: 'success' })
    this.load()
  },

  async punch() {
    if (this.data.isRealMode) {
      wx.showToast({ title: '真实打卡由 Mac 摄像头完成', icon: 'none' })
      return
    }
    const result = await punchDemo()
    const deductionStatus = result.punch.deduction_status as string
    wx.showToast({ title: deductionStatus === 'deducted' ? '已打卡消课' : '已记录打卡', icon: 'none' })
    getApp<IAppOption>().globalData.demoState = result.state
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
    getApp<IAppOption>().globalData.demoState = result.state
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
