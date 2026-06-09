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
    isRealMode: true,
    studentName: '',
    balanceText: '0.00课时',
    ledgers: [] as Array<Record<string, unknown>>
  },

  onShow() {
    this.load()
  },

  async load() {
    const role = getApp<IAppOption>().globalData.currentRole
    if (!role?.studentId) {
      wx.showToast({ title: '请先登录学员身份', icon: 'none' })
      return
    }
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
  }
})
