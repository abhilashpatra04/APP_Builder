import { useState } from 'react';

interface Task {
  id: number;
  title: string;
  description: string;
}

const useTasks = () => {
  const [tasks, setTasks] = useState<Task[]>([]);

  const addTask = (task: Task) => {
    setTasks((prevTasks) => [...prevTasks, task]);
  };

  const removeTask = (id: number) => {
    setTasks((prevTasks) => prevTasks.filter((task) => task.id !== id));
  };

  const editTask = (id: number, updatedTask: Task) => {
    setTasks((prevTasks) => prevTasks.map((task) => (task.id === id ? updatedTask : task)));
  };

  return { tasks, addTask, removeTask, editTask };
};

export default useTasks;
