import { request } from './api'

export function getTeacherDashboard() {
  return request('/teacher/dashboard')
}

