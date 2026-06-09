import { request } from './api'

export function getCampusDashboard() {
  return request('/campus/dashboard')
}

export function getCampusStudents() {
  return request('/campus/students')
}

