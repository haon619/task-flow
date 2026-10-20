import { useEffect, useState } from 'react'
import { createTask, listTasks } from './api'
import Board from './components/Board'
import TaskForm from './components/TaskForm'
import type { Task } from './types'

type LoadState = 'loading' | 'ready' | 'error'

function App() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loadState, setLoadState] = useState<LoadState>('loading')
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
      .catch(() => {
        // 실패하면 화면의 카드 표시는 바꾸지 않는다.
        if (!cancelled) setLoadState('error')
      })
    return () => {
      cancelled = true
    }
  }, [reloadKey])

  function reload() {
    setLoadState('loading')
    setReloadKey((k) => k + 1)
  }

  async function handleCreate(title: string, description: string) {
    const created = await createTask(title, description)
    setTasks((prev) => [...prev, created])
  }

  return (
    <main>
      <h1>Task Flow</h1>

      <TaskForm disabled={loadState !== 'ready'} onCreate={handleCreate} />

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

      <Board tasks={tasks} />
    </main>
  )
}

export default App
