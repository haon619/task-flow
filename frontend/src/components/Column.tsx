import type { Task } from '../types'
import TaskCard from './TaskCard'

interface Props {
  label: string
  tasks: Task[]
}

function Column({ label, tasks }: Props) {
  return (
    <section className="column">
      <h2>{label}</h2>
      <ul>
        {tasks.map((task) => (
          <TaskCard key={task.id} task={task} />
        ))}
      </ul>
    </section>
  )
}

export default Column
