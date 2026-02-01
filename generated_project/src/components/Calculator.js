import React, { useState } from 'react';
import Display from './Display';
import Keypad from './Keypad';
import calculate from '../utils/calculate';

const Calculator = () => {
  const [total, setTotal] = useState('');
  const [next, setNext] = useState(null);
  const [operation, setOperation] = useState(null);

  const handleClick = (buttonName) => {
    const result = calculate({ total, next, operation }, buttonName);

    setTotal(result.total);
    setNext(result.next);
    setOperation(result.operation);
  };

  return (
    <div className="calculator">
      <Display value={total} />
      <Keypad onClick={handleClick} />
    </div>
  );
};

export default Calculator;
