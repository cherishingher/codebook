import { request } from './api'

export type DemoLedger = {
  id: number
  change_type: string
  change_hours: number
  balance_before: number
  balance_after: number
  source: string
  reason?: string
  created_at?: string
}

export type DemoLessonStudent = {
  id: number
  lesson_id: number
  student_id: number
  attendance_status: string
  deduction_status: string
  deducted_hours: number
  note?: string
}

export type DemoState = {
  campus: { id: number; name: string; code: string }
  student: { id: number; name: string; student_no: string }
  course: { id: number; name: string; default_hour_cost: number }
  teacher: { id: number; name: string; title?: string }
  device: { id: number; device_code: string; name: string; location_name?: string; status: string }
  account: { id: number; balance_hours: number; status: string }
  lesson_students: DemoLessonStudent[]
  ledgers: DemoLedger[]
}

export function seedDemo() {
  return request<DemoState>('/demo/seed', { method: 'POST' })
}

export function getDemoState() {
  return request<DemoState>('/demo/state')
}

export function createDemoLesson() {
  return request<DemoState>('/demo/new-lesson', { method: 'POST' })
}

export function punchDemo() {
  return request<{ punch: Record<string, unknown>; state: DemoState }>('/demo/punch', { method: 'POST' })
}

export function runAbsenceDemo() {
  return request<{ created: number; state: DemoState }>('/demo/absence-job', { method: 'POST' })
}

