import React from 'react';
import ReactDOM from 'react-dom';
import TodoList from './TodoList';

const rootElement = document.getElementById('root');
ReactDOM.render(
  <React.StrictMode>
    <TodoList />
  </React.StrictMode>,
  rootElement
);
