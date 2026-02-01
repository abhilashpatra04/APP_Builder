import React from 'react';
import { useTasks } from '../hooks/useTasks';
import Task from './Task';

interface TaskListProps {
  // Add any props if needed
}

const TaskList: React.FC<TaskListProps> = () => {
  const { tasks, error, isLoading } = useTasks();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return (
    <div>
      {tasks.map((task) => (
        <Task key={task.id} task={task} />
      ))}
    </div>
  );
};

export default TaskList;
