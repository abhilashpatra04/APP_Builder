import React from 'react';
import Display from './Display';
import './Keypad.css';

const Keypad = () => {
  const [expression, setExpression] = React.useState('');
  const [result, setResult] = React.useState('');

  const handleButtonPress = (buttonValue) => {
    if (buttonValue === '=') {
      try {
        const result = eval(expression);
        setResult(result.toString());
      } catch (error) {
        setResult('Error');
      }
    } else if (buttonValue === 'C') {
      setExpression('');
      setResult('');
    } else {
      setExpression(expression + buttonValue);
    }
  };

  return (
    <div className="keypad">
      <Display expression={expression} result={result} />
      <div className="button-row">
        <button onClick={() => handleButtonPress('7')}>7</button>
        <button onClick={() => handleButtonPress('8')}>8</button>
        <button onClick={() => handleButtonPress('9')}>9</button>
        <button onClick={() => handleButtonPress('/')}>/</button>
      </div>
      <div className="button-row">
        <button onClick={() => handleButtonPress('4')}>4</button>
        <button onClick={() => handleButtonPress('5')}>5</button>
        <button onClick={() => handleButtonPress('6')}>6</button>
        <button onClick={() => handleButtonPress('*')}>*</button>
      </div>
      <div className="button-row">
        <button onClick={() => handleButtonPress('1')}>1</button>
        <button onClick={() => handleButtonPress('2')}>2</button>
        <button onClick={() => handleButtonPress('3')}>3</button>
        <button onClick={() => handleButtonPress('-')}>-</button>
      </div>
      <div className="button-row">
        <button onClick={() => handleButtonPress('0')}>0</button>
        <button onClick={() => handleButtonPress('.')}>.</button>
        <button onClick={() => handleButtonPress('=')}>=</button>
        <button onClick={() => handleButtonPress('+')}>+</button>
      </div>
      <div className="button-row">
        <button onClick={() => handleButtonPress('C')}>C</button>
      </div>
    </div>
  );
};

export default Keypad;
