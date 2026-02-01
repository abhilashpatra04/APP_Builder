import React, { useState, useEffect } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import TaskList from './TaskList';
import AddTask from './AddTask';
import EditTask from './EditTask';

function App() {
  const [tasks, setTasks] = useState([]);
  const [editing, setEditing] = useState(false);
  const [currentTask, setCurrentTask] = useState({});

  useEffect(() => {
    // Fetch tasks from API or local storage
    const fetchedTasks = JSON.parse(localStorage.getItem('tasks') || '[]');
    setTasks(fetchedTasks);
  }, []);

  const handleAddTask = (newTask) => {
    setTasks([...tasks, newTask]);
    localStorage.setItem('tasks', JSON.stringify([...tasks, newTask]));
  };

  const handleEditTask = (id) => {
    const taskToEdit = tasks.find((task) => task.id === id);
    setEditing(true);
    setCurrentTask(taskToEdit);
  };

  const handleUpdateTask = (updatedTask) => {
    const updatedTasks = tasks.map((task) => (task.id === updatedTask.id ? updatedTask : task));
    setTasks(updatedTasks);
    setEditing(false);
    localStorage.setItem('tasks', JSON.stringify(updatedTasks));
  };

  const handleDeleteTask = (id) => {
    const filteredTasks = tasks.filter((task) => task.id !== id);
    setTasks(filteredTasks);
    localStorage.setItem('tasks', JSON.stringify(filteredTasks));
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <>
              <TaskList tasks={tasks} handleEditTask={handleEditTask} handleDeleteTask={handleDeleteTask} />
              <AddTask handleAddTask={handleAddTask} />
            </>
          }
        />
        <Route
          path="/edit/:id"
          element={
            <EditTask
              currentTask={currentTask}
              handleUpdateTask={handleUpdateTask}
              editing={editing}
            />
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
