import { STATUSES } from '../types'
import type { Task, TaskStatus } from '../types'
import Column from './Column'

interface Props {
  tasks: Task[]
  onStatusChange: (id: number, status: TaskStatus) => Promise<void>
  onUpdate: (id: number, title: string, description: string) => Promise<void>
  onDelete: (id: number) => Promise<void>
}

function Board({ tasks, onStatusChange, onUpdate, onDelete }: Props) {
  return (
    <div className="board">
      {STATUSES.map(({ value, label }) => (
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
