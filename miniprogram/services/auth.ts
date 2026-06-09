import { request } from './api'

export type RoleOption = {
  role: string
  campus_id?: number
  campus_name?: string
  student_id?: number
  teacher_id?: number
}

export async function loginWithCode(code: string) {
  return request<{ token: string; roles: RoleOption[] }>('/auth/wechat-login', {
    method: 'POST',
    data: { code }
  })
}

export async function switchRole(role: RoleOption) {
  return request<{ token: string }>('/auth/switch-role', {
    method: 'POST',
    data: role as unknown as Record<string, unknown>
  })
}

export async function localLogin(params: {
  openid: string
  name?: string
  role: string
  campus_id?: number
  student_id?: number
  teacher_id?: number
}) {
  return request<{ token: string; roles: RoleOption[] }>('/auth/local-login', {
    method: 'POST',
    data: params as unknown as Record<string, unknown>
  })
}
