import React, { useState, useEffect } from 'react';
import calculate from '../utils/calculate';

const Display = () => {
  const [result, setResult] = useState('');
  const [expression, setExpression] = useState('');
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const calculateResult = () => {
      const result = calculate(expression);
      setResult(result);
    };
    calculateResult();
  }, [expression]);

  const handleExpressionChange = (newExpression) => {
    setExpression(newExpression);
  };

  const handleHistoryUpdate = (newHistory) => {
    setHistory(newHistory);
  };

  return (
    <div>
      <input type="text" value={result} readOnly />
      <div>
        {history.map((item, index) => (
          <p key={index}>{item}</p>
        ))}
      </div>
    </div>
  );
};

export default Display;
