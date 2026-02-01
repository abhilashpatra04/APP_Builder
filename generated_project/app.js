// Get DOM references
const timerDisplay = document.getElementById('timer-display');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const resetBtn = document.getElementById('reset-btn');

// Define timer logic
let elapsedTime = 0;
let intervalId = null;
let isRunning = false;

// Function to start the timer
function startTimer() {
  intervalId = setInterval(updateTimer, 1000);
  isRunning = true;
}

// Function to stop the timer
function stopTimer() {
  clearInterval(intervalId);
  isRunning = false;
}

// Function to reset the timer
function resetTimer() {
  elapsedTime = 0;
  updateTimer();
}

// Function to update the timer display
function updateTimer() {
  const hours = Math.floor(elapsedTime / 3600);
  const minutes = Math.floor((elapsedTime % 3600) / 60);
  const seconds = elapsedTime % 60;
  const formattedTime = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  timerDisplay.textContent = formattedTime;
  elapsedTime++;
}

// Function to calculate and display lap time
function lapTime() {
  const currentLapTime = elapsedTime;
  console.log(`Lap time: ${currentLapTime} seconds`);
}

// Add event listeners
startBtn.addEventListener('click', startTimer);
stopBtn.addEventListener('click', stopTimer);
resetBtn.addEventListener('click', resetTimer);

// Call updateTimer initially
updateTimer();
