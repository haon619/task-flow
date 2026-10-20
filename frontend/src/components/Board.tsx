import { STATUSES } from '../types'
import type { Task, TaskInput, TaskStatus } from '../types'
import Column from './Column'

interface Props {
  tasks: Task[]
  // 상태 필터로 고른 열만 보여 준다. 'ALL'이면 세 열 모두.
  visibleStatus: TaskStatus | 'ALL'
  onStatusChange: (id: number, status: TaskStatus) => Promise<void>
  onUpdate: (id: number, input: TaskInput) => Promise<void>
  onDelete: (id: number) => Promise<void>
}

function Board({ tasks, visibleStatus, onStatusChange, onUpdate, onDelete }: Props) {
  const columns = STATUSES.filter(
    ({ value }) => visibleStatus === 'ALL' || value === visibleStatus,
  )
  return (
    <div className="board">
      {columns.map(({ value, label }) => (
        <Column
          key={value}
          label={label}
          tasks={tasks.filter((t) => t.status === value)}
          onStatusChange={onStatusChange}
          onUpdate={onUpdate}
          onDelete={onDelete}
        />
      ))}
    </div>
  )
}

export default Board
