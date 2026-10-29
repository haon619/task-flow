import { useEffect, useState } from 'react'
import {
  ApiError,
  createTask,
  deleteTask,
  listTasks,
  updateTask,
  updateTaskStatus,
} from './api'
import Board from './components/Board'
import FilterBar from './components/FilterBar'
import TaskForm from './components/TaskForm'
import { filterTasks, isFiltering, NO_FILTERS } from './filter'
import type { Filters } from './filter'
import type { Task, TaskInput, TaskStatus } from './types'

type LoadState = 'loading' | 'ready' | 'error'

function BoardScreen({ onUnauthorized }: { onUnauthorized: () => void }) {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [filters, setFilters] = useState<Filters>(NO_FILTERS)
  // 값을 바꾸면 목록을 다시 불러온다.
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    listTasks()
      .then((list) => {
        if (cancelled) return
        setTasks(list)
        setLoadState('ready')
      })
      .catch((err) => {
        if (err instanceof ApiError && err.kind === 'unauthorized') onUnauthorized()
        // 실패하면 화면의 카드 표시는 바꾸지 않는다.
        if (!cancelled) setLoadState('error')
      })
    return () => {
      cancelled = true
    }
  }, [reloadKey, onUnauthorized])

  function reload() {
    setLoadState('loading')
    setReloadKey((k) => k + 1)
  }

  // 순서와 기한 초과 표시는 서버가 정한다. 바꾼 뒤에는 목록을 다시 받아 서버 순서를 그대로 쓴다.
  // 다시 받지 못하면 응답으로 받은 카드만 반영한다.
  async function refresh(fallback: (prev: Task[]) => Task[]) {
    try {
      setTasks(await listTasks())
    } catch {
      setTasks(fallback)
    }
  }

  async function handleCreate(input: TaskInput) {
    const created = await createTask(input)
    await refresh((prev) => [...prev, created])
  }

  // 대상 카드가 이미 없으면 목록을 다시 불러와 맞춘다. 오류는 카드가 안내하도록 다시 던진다.
  function syncIfMissing(err: unknown): never {
    if (err instanceof ApiError && err.kind === 'not_found') reload()
    throw err
  }

  async function handleStatusChange(id: number, status: TaskStatus) {
    try {
      const updated = await updateTaskStatus(id, status)
      await refresh((prev) => prev.map((t) => (t.id === id ? updated : t)))
    } catch (err) {
      syncIfMissing(err)
    }
  }

  async function handleUpdate(id: number, input: TaskInput) {
    try {
      const updated = await updateTask(id, input)
      await refresh((prev) => prev.map((t) => (t.id === id ? updated : t)))
    } catch (err) {
      syncIfMissing(err)
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteTask(id)
      setTasks((prev) => prev.filter((t) => t.id !== id))
    } catch (err) {
      syncIfMissing(err)
    }
  }

  const visibleTasks = filterTasks(tasks, filters)

  return (
    <main>
      <h1>Task Flow</h1>

      <TaskForm disabled={loadState !== 'ready'} onCreate={handleCreate} />

      <FilterBar filters={filters} onChange={setFilters} />

      {loadState === 'loading' && <p className="notice">불러오는 중…</p>}
      {loadState === 'error' && (
        <p className="notice error" role="alert">
          카드를 불러오지 못했습니다.{' '}
          <button type="button" onClick={reload}>
            다시 불러오기
          </button>
        </p>
      )}
      {loadState === 'ready' && tasks.length === 0 && (
        <p className="notice">아직 카드가 없습니다. 위에서 첫 카드를 등록해 보세요.</p>
      )}

      {loadState === 'ready' &&
        tasks.length > 0 &&
        visibleTasks.length === 0 &&
        isFiltering(filters) && (
          <p className="notice">조건에 맞는 카드가 없습니다.</p>
        )}

      <Board
        tasks={visibleTasks}
        visibleStatus={filters.status}
        onStatusChange={handleStatusChange}
        onUpdate={handleUpdate}
        onDelete={handleDelete}
      />
    </main>
  )
}

export default BoardScreen
