export function formatHours(value: number): string {
  return `${value.toFixed(2)}课时`
}

export function attendanceText(value: string): string {
  const map: Record<string, string> = {
    pending: '待确认',
    present: '到课',
    late: '迟到',
    absent: '缺勤',
    leave: '请假',
    exception: '异常'
  }
  return map[value] || value
}

export function deductionText(value: string): string {
  const map: Record<string, string> = {
    pending: '待处理',
    deducted: '已消课',
    not_deducted: '未消课',
    manual_required: '需确认',
    voided: '已作废'
  }
  return map[value] || value
}

export function ledgerText(value: string): string {
  const map: Record<string, string> = {
    add: '加课',
    deduct: '消课',
    refund: '退课',
    adjust: '修正',
    void: '作废',
    restore: '恢复'
  }
  return map[value] || value
}

export function signedHours(value: number): string {
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}`
}
