import { getDemoState } from '../../../services/demo'
import { formatHours, ledgerText, signedHours } from '../../../utils/format'

Page({
  data: {
    studentName: '',
    balanceText: '0.00课时',
    ledgers: [] as Array<Record<string, unknown>>
  },

  onShow() {
    this.load()
  },

  async load() {
    const state = await getDemoState()
    this.setData({
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
