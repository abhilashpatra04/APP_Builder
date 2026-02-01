import React, { useState } from 'react';
import './NumberInput.css';

const NumberInput = () => {
  const [value, setValue] = useState('');
  const [isDecimal, setIsDecimal] = useState(false);

  const handleInputChange = (e) => {
    const inputValue = e.target.value;
    if (inputValue === '' || inputValue === '-') {
      setValue(inputValue);
    } else if (!isNaN(inputValue) || (inputValue.includes('.') && !isDecimal)) {
      if (inputValue.includes('.')) {
        setIsDecimal(true);
      }
      setValue(inputValue);
    }
  };

  const handleCalculatorIntegration = () => {
    // TO DO: integrate with Calculator.js
  };

  return (
    <div className="number-input">
      <input
        type="text"
        value={value}
        onChange={handleInputChange}
        placeholder="Enter a number"
      />
      <button onClick={handleCalculatorIntegration}>Calculate</button>
    </div>
  );
};

export default NumberInput;
