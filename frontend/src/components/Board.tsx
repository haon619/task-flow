import { STATUSES } from '../types'
import type { Task } from '../types'
import Column from './Column'

function Board({ tasks }: { tasks: Task[] }) {
  return (
    <div className="board">
      {STATUSES.map(({ value, label }) => (
        <Column
          key={value}
          label={label}
          tasks={tasks.filter((t) => t.status === value)}
        />
      ))}
    </div>
  )
}

export default Board
