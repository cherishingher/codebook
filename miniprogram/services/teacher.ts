import { request } from './api'
import type { LessonCreatePayload } from './campus'

export function getTeacherDashboard(teacherId: number) {
  return request(`/teacher/dashboard?teacher_id=${teacherId}`)
}

export function getTeacherLessons(teacherId: number) {
  return request(`/teacher/lessons?teacher_id=${teacherId}`)
}

export function getTeacherLessonDetail(teacherId: number, lessonId: number) {
  return request(`/teacher/lessons/${lessonId}?teacher_id=${teacherId}`)
}

export function createTeacherLesson(payload: LessonCreatePayload) {
  return request('/teacher/lessons', {
    method: 'POST',
    data: payload as unknown as Record<string, unknown>
  })
}

export function confirmAttendance(params: {
  lessonId: number
  studentId: number
  teacherId?: number
  attendanceStatus: string
  deductionAction: string
  reason: string
}) {
  return request(`/teacher/lessons/${params.lessonId}/attendance/confirm`, {
    method: 'POST',
    data: {
      student_id: params.studentId,
      teacher_id: params.teacherId,
      attendance_status: params.attendanceStatus,
      deduction_action: params.deductionAction,
      reason: params.reason
    }
  })
}
