import { createDemoLesson, getDemoState, punchDemo, runAbsenceDemo, seedDemo } from '../../../services/demo'
import { formatHours } from '../../../utils/format'

Page({
  data: {
    campusName: '',
    deviceName: '',
    deviceStatus: '',
    balanceText: '0.00课时'
  },

  onShow() {
    this.load()
  },

  async load() {
    const state = await getDemoState().catch(() => seedDemo())
    getApp<IAppOption>().globalData.demoState = state
    this.setData({
      campusName: state.campus.name,
      deviceName: state.device.name,
      deviceStatus: state.device.status === 'active' ? '在线' : state.device.status,
      balanceText: formatHours(Number(state.account.balance_hours))
    })
  },

  async newLesson() {
    await createDemoLesson()
    wx.showToast({ title: '已新建课次', icon: 'success' })
    this.load()
  },

  async punch() {
    const result = await punchDemo()
    const deductionStatus = result.punch.deduction_status as string
    wx.showToast({ title: deductionStatus === 'deducted' ? '已打卡消课' : '已记录打卡', icon: 'none' })
    getApp<IAppOption>().globalData.demoState = result.state
    this.load()
  },

  async runAbsence() {
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
