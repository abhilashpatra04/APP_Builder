import React, { useState } from 'react';
import { useTasks } from '../hooks/useTasks';
import { Task } from '../types/Task';

interface EditTaskProps {
  task: Task;
  onClose: () => void;
}

const EditTask: React.FC<EditTaskProps> = ({ task, onClose }) => {
  const { updateTask } = useTasks();
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const updatedTask: Task = { ...task, title, description };
    updateTask(updatedTask);
    onClose();
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Title:
        <input type="text" value={title} onChange={(event) => setTitle(event.target.value)} />
      </label>
      <label>
        Description:
        <textarea value={description} onChange={(event) => setDescription(event.target.value)} />
      </label>
      <button type="submit">Update Task</button>
    </form>
  );
};

export default EditTask;
