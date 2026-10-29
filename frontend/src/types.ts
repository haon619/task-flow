export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'DONE'

export type Priority = 'LOW' | 'NORMAL' | 'HIGH'

// 카드 입력값. 등록과 수정에서 같이 쓴다.
export interface TaskInput {
  title: string
  description: string
  priority: Priority
  assignee: string
}

export interface Task extends TaskInput {
  id: number
  status: TaskStatus
  due_date: string | null
}

export const PRIORITIES: { value: Priority; label: string }[] = [
  { value: 'LOW', label: '낮음' },
  { value: 'NORMAL', label: '보통' },
  { value: 'HIGH', label: '높음' },
]

export const ASSIGNEE_MAX_LENGTH = 50

// 열 순서와 화면 표시 이름 (PRD: 할 일 · 진행 중 · 완료)
export const STATUSES: { value: TaskStatus; label: string }[] = [
  { value: 'TODO', label: '할 일' },
  { value: 'IN_PROGRESS', label: '진행 중' },
  { value: 'DONE', label: '완료' },
]
