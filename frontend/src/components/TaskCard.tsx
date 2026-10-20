import { useState } from 'react'
import type { FormEvent } from 'react'
import { ASSIGNEE_MAX_LENGTH, PRIORITIES, STATUSES } from '../types'
import type { Priority, Task, TaskInput, TaskStatus } from '../types'

interface Props {
  task: Task
  onStatusChange: (id: number, status: TaskStatus) => Promise<void>
  onUpdate: (id: number, input: TaskInput) => Promise<void>
  onDelete: (id: number) => Promise<void>
}

function TaskCard({ task, onStatusChange, onUpdate, onDelete }: Props) {
  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState(task.title)
  const [description, setDescription] = useState(task.description)
  const [priority, setPriority] = useState<Priority>(task.priority)
  const [assignee, setAssignee] = useState(task.assignee)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  function startEdit() {
    // 기존 값을 채워서 시작한다.
    setTitle(task.title)
    setDescription(task.description)
    setPriority(task.priority)
    setAssignee(task.assignee)
    setError(null)
    setEditing(true)
  }

  async function run(action: () => Promise<void>): Promise<boolean> {
    setBusy(true)
    setError(null)
    try {
      await action()
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : '처리하지 못했습니다.')
      return false
    } finally {
      setBusy(false)
    }
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault()
    // 화면 쪽 검사: 제목이 비었으면 요청 없이 안내한다. 최종 판단은 API.
    if (title.trim() === '') {
      setError('제목을 입력해 주세요.')
      return
    }
    const ok = await run(() =>
      onUpdate(task.id, { title: title.trim(), description, priority, assignee: assignee.trim() }),
    )
    if (ok) setEditing(false)
  }

  async function handleDelete() {
    // D-013: 삭제 전에 한 번 묻는다.
    if (!window.confirm(`"${task.title}" 카드를 삭제할까요?`)) return
    await run(() => onDelete(task.id))
  }

  if (editing) {
    return (
      <li className="card">
        <form className="edit-form" onSubmit={handleSave} noValidate>
          <input
            aria-label="제목"
            value={title}
            disabled={busy}
            onChange={(e) => setTitle(e.target.value)}
          />
          <input
            aria-label="설명"
            value={description}
            disabled={busy}
            onChange={(e) => setDescription(e.target.value)}
          />
          <label className="field">
            우선순위
            <select
              value={priority}
              disabled={busy}
              onChange={(e) => setPriority(e.target.value as Priority)}
            >
              {PRIORITIES.map(({ value, label }) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <input
            aria-label="담당자"
            placeholder="담당자 (선택)"
            maxLength={ASSIGNEE_MAX_LENGTH}
            value={assignee}
            disabled={busy}
            onChange={(e) => setAssignee(e.target.value)}
          />
          <div className="card-actions">
            <button type="submit" disabled={busy}>
              저장
            </button>
            <button type="button" disabled={busy} onClick={() => setEditing(false)}>
              취소
            </button>
          </div>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </form>
      </li>
    )
  }

  const priorityLabel = PRIORITIES.find((p) => p.value === task.priority)?.label

  return (
    <li className="card">
      <strong>{task.title}</strong>
      {(task.priority !== 'NONE' || task.assignee) && (
        <p className="meta">
          {task.priority !== 'NONE' && (
            <span className={`badge badge-${task.priority.toLowerCase()}`}>
              우선순위 {priorityLabel}
            </span>
          )}
          {task.assignee && <span className="assignee">담당 {task.assignee}</span>}
        </p>
      )}
      {task.description && <p>{task.description}</p>}
      <div className="card-actions">
        {/* 고르기 전에는 바뀌지 않는다. 요청이 성공해야 카드가 옮겨진다. */}
        <select
          aria-label="상태"
          value={task.status}
          disabled={busy}
          onChange={(e) => void run(() => onStatusChange(task.id, e.target.value as TaskStatus))}
        >
          {STATUSES.map(({ value, label }) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <button type="button" disabled={busy} onClick={startEdit}>
          수정
        </button>
        <button type="button" disabled={busy} onClick={() => void handleDelete()}>
          삭제
        </button>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </li>
  )
}

export default TaskCard
