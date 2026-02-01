import React, { useState } from 'react';
import { useTasks } from '../hooks/useTasks';

interface Task {
  id: number;
  title: string;
  description: string;
}

const AddTask: React.FC = () => {
  const { addTask } = useTasks();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState(null);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!title || !description) {
      setError('Please fill in all fields');
      return;
    }
    const newTask: Task = {
      id: Date.now(),
      title,
      description,
    };
    addTask(newTask);
    setTitle('');
    setDescription('');
    setError(null);
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
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <button type="submit">Add Task</button>
    </form>
  );
};

export default AddTask;
