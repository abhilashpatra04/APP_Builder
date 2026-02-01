import React from 'react';

interface TaskProps {
  task: {
    id: number;
    title: string;
    description: string;
  };
  onDelete: (id: number) => void;
  onEdit: (id: number) => void;
}

const Task: React.FC<TaskProps> = ({ task, onDelete, onEdit }) => {
  const handleDelete = () => {
    onDelete(task.id);
  };

  const handleEdit = () => {
    onEdit(task.id);
  };

  return (
    <div>
      <h2>{task.title}</h2>
      <p>{task.description}</p>
      <button onClick={handleDelete}>Delete</button>
      <button onClick={handleEdit}>Edit</button>
    </div>
  );
};

export default Task;
