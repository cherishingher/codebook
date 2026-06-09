import { request } from './api'

export function getLearnerDashboard(studentId: number) {
  return request(`/learner/dashboard?student_id=${studentId}`)
}

export function getLearnerLessons(studentId: number, startDate?: string, endDate?: string) {
  const startPart = startDate ? `&start_date=${encodeURIComponent(startDate)}` : ''
  const endPart = endDate ? `&end_date=${encodeURIComponent(endDate)}` : ''
  return request(`/learner/lessons?student_id=${studentId}${startPart}${endPart}`)
}

export function getLearnerLessonDetail(studentId: number, lessonId: number) {
  return request(`/learner/lessons/${lessonId}?student_id=${studentId}`)
}

export function getLearnerHourAccounts(studentId: number) {
  return request(`/learner/hour-accounts?student_id=${studentId}`)
}

export function getLearnerLedgers(studentId: number) {
  return request(`/learner/hour-ledgers?student_id=${studentId}`)
}
