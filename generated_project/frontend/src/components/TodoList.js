import React from 'react';
import Todo from '../models/Todo';

const TodoList = () => {
  const [todos, setTodos] = React.useState([]);

  React.useEffect(() => {
    fetch('/api/todos')
      .then(response => response.json())
      .then(data => setTodos(data));
  }, []);

  return (
    <ul>
      {todos.map(todo => (
        <li key={todo.id}>{todo.title}</li>
      ))}
    </ul>
  );
};

export default TodoList;
