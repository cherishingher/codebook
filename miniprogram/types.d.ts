interface IAppOption {
  globalData: {
    apiBaseUrl: string
    token: string
    currentRole: null | {
      role: string
      campusId?: number
      studentId?: number
      teacherId?: number
    }
    demoState: null | {
      campus: { id: number; name: string; code: string }
      student: { id: number; name: string; student_no: string }
      course: { id: number; name: string; default_hour_cost: number }
      teacher: { id: number; name: string; title?: string }
      device: { id: number; device_code: string; name: string; location_name?: string; status: string }
      account: { id: number; balance_hours: number; status: string }
      lesson_students: Array<{
        id: number
        lesson_id: number
        student_id: number
        attendance_status: string
        deduction_status: string
        deducted_hours: number
        note?: string
      }>
      ledgers: Array<{
        id: number
        change_type: string
        change_hours: number
        balance_before: number
        balance_after: number
        source: string
        reason?: string
        created_at?: string
      }>
    }
  }
}
