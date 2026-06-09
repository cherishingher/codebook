import { getDemoState } from '../../../services/demo'
import { getLearnerHourAccounts, getLearnerLedgers } from '../../../services/learner'
import { formatHours, ledgerText, signedHours } from '../../../utils/format'

type AccountItem = { balance_hours: number }
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
    isRealMode: false,
    studentName: '',
    balanceText: '0.00课时',
    ledgers: [] as Array<Record<string, unknown>>
  },

  onShow() {
    this.load()
  },

  async load() {
    const role = getApp<IAppOption>().globalData.currentRole
    if (role?.studentId) {
      try {
        const [accountsRes, ledgersRes] = await Promise.all([
          getLearnerHourAccounts(role.studentId) as Promise<{ items: AccountItem[] }>,
          getLearnerLedgers(role.studentId) as Promise<{ items: LedgerItem[] }>
        ])
        const totalBalance = accountsRes.items.reduce((sum, item) => sum + Number(item.balance_hours), 0)
        this.setData({
          isRealMode: true,
          studentName: `学员 #${role.studentId}`,
          balanceText: formatHours(totalBalance),
          ledgers: ledgersRes.items.map((item) => ({
            ...item,
            typeText: ledgerText(item.change_type),
            changeText: signedHours(Number(item.change_hours))
          }))
        })
        return
      } catch (error) {
        wx.showToast({ title: '真实课时读取失败，显示演示数据', icon: 'none' })
      }
    }
    const state = await getDemoState()
    this.setData({
      isRealMode: false,
      studentName: state.student.name,
      balanceText: formatHours(Number(state.account.balance_hours)),
      ledgers: state.ledgers.map((item) => ({
        ...item,
        typeText: ledgerText(item.change_type),
        changeText: signedHours(Number(item.change_hours))
      }))
    })
  }
})
