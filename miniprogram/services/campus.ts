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

export type StudentCreatePayload = {
  campus_id: number
  name: string
  student_no?: string
  phone?: string
}

export type TeacherCreatePayload = {
  campus_id: number
  name: string
  phone?: string
  title?: string
}

export type CourseCreatePayload = {
  campus_id: number
  name: string
  subject?: string
  default_duration?: number
  default_hour_cost?: string
}

export type HourAccountCreatePayload = {
  campus_id: number
  student_id: number
  course_id: number
  initial_hours: string
  reason: string
}

export function getCampusDashboard(campusId: number) {
  return request(`/campus/dashboard?campus_id=${campusId}`)
}

export function getCampusStudents(campusId: number, keyword = '') {
  const keywordPart = keyword ? `&keyword=${encodeURIComponent(keyword)}` : ''
  return request(`/campus/students?campus_id=${campusId}${keywordPart}`)
}

export function createCampusStudent(payload: StudentCreatePayload) {
  return request('/campus/students', {
    method: 'POST',
    data: payload as unknown as Record<string, unknown>
  })
}

export function getCampusTeachers(campusId: number) {
  return request(`/campus/teachers?campus_id=${campusId}`)
}

export function createCampusTeacher(payload: TeacherCreatePayload) {
  return request('/campus/teachers', {
    method: 'POST',
    data: payload as unknown as Record<string, unknown>
  })
}

export function getCampusCourses(campusId: number) {
  return request(`/campus/courses?campus_id=${campusId}`)
}

export function createCampusCourse(payload: CourseCreatePayload) {
  return request('/campus/courses', {
    method: 'POST',
    data: payload as unknown as Record<string, unknown>
  })
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

export function createCampusHourAccount(payload: HourAccountCreatePayload) {
  return request('/campus/hour-accounts', {
    method: 'POST',
    data: payload as unknown as Record<string, unknown>
  })
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

export function runAbsenceJob() {
  return request<{ created: number }>('/dev/run-absence-job', { method: 'POST' })
}
