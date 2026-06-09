import { request } from './api'

export type LessonCreatePayload = {
  campus_id: number
  course_id: number
  teacher_id: number
  title: string
  classroom_name?: string
  start_time: string
  end_time: string
  checkin_start_time: string
  checkin_end_time: string
  late_after_time: string
  default_hour_cost: string
  student_ids: number[]
}

export type DeductionRulePayload = {
  campus_id: number
  scope_type: 'campus' | 'course' | 'lesson' | 'teacher'
  scope_id?: number
  present_action: 'deduct' | 'not_deduct' | 'manual_required'
  late_action: 'deduct' | 'not_deduct' | 'manual_required'
  absent_action: 'deduct' | 'not_deduct' | 'manual_required'
  leave_action: 'deduct' | 'not_deduct' | 'manual_required'
  exception_action: 'deduct' | 'not_deduct' | 'manual_required'
}

export function getCampusDashboard(campusId: number) {
  return request(`/campus/dashboard?campus_id=${campusId}`)
}

export function getCampusStudents(campusId: number, keyword = '') {
  const keywordPart = keyword ? `&keyword=${encodeURIComponent(keyword)}` : ''
  return request(`/campus/students?campus_id=${campusId}${keywordPart}`)
}

export function getCampusTeachers(campusId: number) {
  return request(`/campus/teachers?campus_id=${campusId}`)
}

export function getCampusCourses(campusId: number) {
  return request(`/campus/courses?campus_id=${campusId}`)
}

export function getCampusLessons(campusId: number) {
  return request(`/campus/lessons?campus_id=${campusId}`)
}

export function getCampusLessonDetail(campusId: number, lessonId: number) {
  return request(`/campus/lessons/${lessonId}?campus_id=${campusId}`)
}

export function createCampusLesson(payload: LessonCreatePayload) {
  return request('/campus/lessons', {
    method: 'POST',
    data: payload as unknown as Record<string, unknown>
  })
}

export function getCampusHourAccounts(campusId: number, studentId?: number) {
  const studentPart = studentId ? `&student_id=${studentId}` : ''
  return request(`/campus/hour-accounts?campus_id=${campusId}${studentPart}`)
}

export function getCampusHourLedgers(campusId: number, studentId?: number) {
  const studentPart = studentId ? `&student_id=${studentId}` : ''
  return request(`/campus/hour-ledgers?campus_id=${campusId}${studentPart}`)
}

export function addCampusHourLedger(accountId: number, changeHours: string, reason: string) {
  return request(`/campus/hour-accounts/${accountId}/ledger`, {
    method: 'POST',
    data: {
      change_type: 'add',
      change_hours: changeHours,
      reason
    }
  })
}

export function getDeductionRules(campusId: number) {
  return request(`/campus/deduction-rules?campus_id=${campusId}`)
}

export function upsertDeductionRule(payload: DeductionRulePayload) {
  return request('/campus/deduction-rules', {
    method: 'POST',
    data: payload as unknown as Record<string, unknown>
  })
}
