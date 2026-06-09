import { request } from './api'

export function getTeacherDashboard() {
  return request('/teacher/dashboard')
}

export function confirmAttendance(params: {
  lessonId: number
  studentId: number
  attendanceStatus: string
  deductionAction: string
  reason: string
}) {
  return request(`/teacher/lessons/${params.lessonId}/attendance/confirm`, {
    method: 'POST',
    data: {
      student_id: params.studentId,
      attendance_status: params.attendanceStatus,
      deduction_action: params.deductionAction,
      reason: params.reason
    }
  })
}
