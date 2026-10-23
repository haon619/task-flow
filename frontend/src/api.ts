import type { Task, TaskInput, TaskStatus } from './types'

// 화면이 실패를 구분해서 안내할 수 있게 종류를 붙인다.
// not_found: 이미 지운 카드. 화면이 목록을 다시 불러와 맞춘다.
export class ApiError extends Error {
  kind: 'network' | 'invalid' | 'not_found' | 'unauthorized' | 'conflict' | 'server'

  constructor(kind: ApiError['kind'], message: string) {
    super(message)
    this.kind = kind
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(path, init)
  } catch {
    throw new ApiError('network', 'API에 연결할 수 없습니다.')
  }
  if (!res.ok) {
    if (res.status === 422) {
      throw new ApiError('invalid', '입력값이 올바르지 않습니다.')
    }
    if (res.status === 401) {
      throw new ApiError('unauthorized', '로그인이 필요합니다.')
    }
    if (res.status === 409) {
      throw new ApiError('conflict', '이미 있는 아이디입니다.')
    }
    if (res.status === 404) {
      throw new ApiError('not_found', '이미 삭제된 카드입니다. 목록을 다시 불러옵니다.')
    }
    throw new ApiError('server', '저장소에 문제가 생겨 처리하지 못했습니다.')
  }
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

function jsonBody(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

export function listTasks(): Promise<Task[]> {
  return request<Task[]>('/api/tasks')
}

export function createTask(input: TaskInput): Promise<Task> {
  return request<Task>('/api/tasks', jsonBody('POST', input))
}

export function updateTask(id: number, input: TaskInput): Promise<Task> {
  return request<Task>(`/api/tasks/${id}`, jsonBody('PATCH', input))
}

export function updateTaskStatus(id: number, status: TaskStatus): Promise<Task> {
  return request<Task>(`/api/tasks/${id}/status`, jsonBody('PATCH', { status }))
}

export function deleteTask(id: number): Promise<void> {
  return request<void>(`/api/tasks/${id}`, { method: 'DELETE' })
}

export type User = { id: number; username: string }

export function me(): Promise<User> {
  return request<User>('/api/auth/me')
}

export function login(username: string, password: string): Promise<User> {
  return request<User>('/api/auth/login', jsonBody('POST', { username, password }))
}

export function register(username: string, password: string): Promise<User> {
  return request<User>('/api/auth/register', jsonBody('POST', { username, password }))
}

export function logout(): Promise<void> {
  return request<void>('/api/auth/logout', { method: 'POST' })
}
