import type { Task } from './types'

// 화면이 실패를 구분해서 안내할 수 있게 종류를 붙인다.
export class ApiError extends Error {
  kind: 'network' | 'invalid' | 'server'

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
    throw new ApiError('server', '저장소에 문제가 생겨 처리하지 못했습니다.')
  }
  return (await res.json()) as T
}

export function listTasks(): Promise<Task[]> {
  return request<Task[]>('/api/tasks')
}

export function createTask(title: string, description: string): Promise<Task> {
  return request<Task>('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description }),
  })
}
