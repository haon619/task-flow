import { useState } from 'react'
import type { FormEvent } from 'react'

interface Props {
  disabled: boolean
  onCreate: (title: string, description: string) => Promise<void>
}

function TaskForm({ disabled, onCreate }: Props) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    // 화면 쪽 검사: 비었거나 공백뿐이면 요청 없이 안내한다. 최종 판단은 API.
    if (title.trim() === '') {
      setError('제목을 입력해 주세요.')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      await onCreate(title.trim(), description)
      setTitle('')
      setDescription('')
    } catch (err) {
      // 실패하면 입력한 내용을 지우지 않는다.
      setError(err instanceof Error ? err.message : '등록하지 못했습니다.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="task-form" onSubmit={handleSubmit} noValidate>
      <input
        aria-label="제목"
        placeholder="제목 (필수)"
        value={title}
        disabled={disabled || submitting}
        onChange={(e) => setTitle(e.target.value)}
      />
      <input
        aria-label="설명"
        placeholder="설명 (선택)"
        value={description}
        disabled={disabled || submitting}
        onChange={(e) => setDescription(e.target.value)}
      />
      <button type="submit" disabled={disabled || submitting}>
        등록
      </button>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </form>
  )
}

export default TaskForm
