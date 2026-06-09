import { request } from './api'

export function getLearnerDashboard(studentId: number) {
  return request(`/learner/dashboard?student_id=${studentId}`)
}

export function getLearnerLedgers(studentId: number) {
  return request(`/learner/hour-ledgers?student_id=${studentId}`)
}

