import type { Task, TaskStatus } from './types'

export type StatusFilter = TaskStatus | 'ALL'

export interface Filters {
  query: string
  status: StatusFilter
}

export const NO_FILTERS: Filters = { query: '', status: 'ALL' }

export function isFiltering({ query, status }: Filters): boolean {
  return query.trim() !== '' || status !== 'ALL'
}

// 제목 · 설명에서 검색어를 찾고(대소문자 무시), 상태로 거른다. (R-007)
export function filterTasks(tasks: Task[], { query, status }: Filters): Task[] {
  const q = query.trim().toLowerCase()
  return tasks.filter(
    (t) =>
      (status === 'ALL' || t.status === status) &&
      (q === '' ||
        t.title.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q)),
  )
}
