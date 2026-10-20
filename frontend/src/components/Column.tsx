import type { Task, TaskStatus } from '../types'
import TaskCard from './TaskCard'

interface Props {
  label: string
  tasks: Task[]
  onStatusChange: (id: number, status: TaskStatus) => Promise<void>
  onUpdate: (id: number, title: string, description: string) => Promise<void>
  onDelete: (id: number) => Promise<void>
}

function Column({ label, tasks, onStatusChange, onUpdate, onDelete }: Props) {
  return (
    <section className="column">
      <h2>{label}</h2>
      <ul>
        {tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            onStatusChange={onStatusChange}
            onUpdate={onUpdate}
            onDelete={onDelete}
          />
        ))}
      </ul>
    </section>
  )
}

export default Column
