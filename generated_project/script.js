function getUserInput() {
    const userInput = document.getElementById('user-input').value;
    return userInput;
}

function sendRequestToServer(userInput) {
    const url = 'https://example.com/calculate';
    const params = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ input: userInput })
    };
    return fetch(url, params).then(response => response.json());
}

function updateResultDisplay(result) {
    const resultDisplay = document.getElementById('result-display');
    resultDisplay.innerText = result;
}

function handleUserInput() {
    const userInput = getUserInput();
    sendRequestToServer(userInput).then(result => updateResultDisplay(result));
}

document.addEventListener('DOMContentLoaded', function() {
    const submitButton = document.getElementById('submit-button');
    submitButton.addEventListener('click', handleUserInput);
});