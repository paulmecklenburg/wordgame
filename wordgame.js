const AUDIO_ID = 'audioSource';
const INPUT_ID = 'divInput';
const HISTORY_STORAGE_KEY = 'wordgame_history';
const TRACKING_SETTING_KEY = 'wordgame_track_performance';
const EMA_ALPHA = 0.7; // Smoothing factor for EMA
const BASE_WORD_WEIGHT = 1.0; // Base weight for every word

var nextTargetWordInd = 0; // For sequential/shuffled word selection
var targetWord;
var attemptCount;
var performanceHistory = JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY) || '{}');
var isTrackingEnabled = JSON.parse(localStorage.getItem(TRACKING_SETTING_KEY) || 'false');

function savePerformanceHistory() {
  localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(performanceHistory));
}

function saveTrackingSetting() {
  localStorage.setItem(TRACKING_SETTING_KEY, JSON.stringify(isTrackingEnabled));
}

function getPenaltyScore(attempts) {
  if (attempts === 1) return 0.0; // Mastered
  if (attempts === 2) return 0.5; // Mild struggle
  if (attempts >= 3) return 1.0; // Significant struggle
  return 0.0; // Should not happen
}

function updateWordPerformance(word, attempts) {
  if (!isTrackingEnabled) return;

  // New words (not in history) start with a score of 1 (struggled)
  const currentPerformanceScore = performanceHistory[word] !== undefined ? performanceHistory[word] : 1.0;
  const penalty = getPenaltyScore(attempts);

  // Apply Exponential Moving Average
  performanceHistory[word] = (currentPerformanceScore * EMA_ALPHA) + (penalty * (1 - EMA_ALPHA));
  savePerformanceHistory();
}

function getWordByWeightedSelection() {
  let totalWeight = 0;
  const wordWeights = wordList.map(word => {
    // Words not in history get a score of 1, biasing them to be picked more
    const score = performanceHistory[word] !== undefined ? performanceHistory[word] : 1.0;
    // Higher score (more struggle) means higher weight
    const weight = BASE_WORD_WEIGHT + (score * 5); // Multiplier of 5 to increase impact of struggle
    totalWeight += weight;
    return { word, weight };
  });

  let randomPoint = Math.random() * totalWeight;
  for (const { word, weight } of wordWeights) {
    randomPoint -= weight;
    if (randomPoint <= 0) {
      return word;
    }
  }
  // Fallback, should not happen with proper weights
  return wordList[Math.floor(Math.random() * wordList.length)];
}

function setTargetWord(word) {
  console.log('target word: ' + word);
  targetWord = word;
  document.getElementById(AUDIO_ID).src = 'snd/' + word + '.mp3';
  attemptCount = 1;
}

function changeTargetWord() {
  if (isTrackingEnabled) {
    setTargetWord(getWordByWeightedSelection());
  } else {
    // Fallback to original sequential/shuffled logic if tracking is off
    setTargetWord(wordList[nextTargetWordInd]);
    nextTargetWordInd = (nextTargetWordInd + 1) % wordList.length;
  }
}

function updateScoreById(id) {
  el = document.getElementById(id);
  el.textContent = Number(el.textContent) + 1;
  el.classList.remove('pop');
  void el.offsetWidth;
  el.classList.add('pop');
}

function updateScore(attemptCount) {
  if (attemptCount == 1)
    updateScoreById('diamondScore');
  else if (attemptCount == 2)
    updateScoreById('goldScore');
  else if (attemptCount == 3)
    updateScoreById('silverScore');
  else
    updateScoreById('bronzeScore');
}

function tryAddLetter(letter) {
  document.getElementById(INPUT_ID).textContent += letter;
}

function tryRemoveLetter() {
  var elem = document.getElementById(INPUT_ID)
  elem.textContent = elem.textContent.slice(0, -1);
}

function tryWordDone() {
  var inputText = document.getElementById(INPUT_ID).textContent;
  if (inputText.length < 1) return;
  console.log(inputText);

  var historyDiv = document.getElementById('history'); // Renamed from 'history' to 'historyDiv' to avoid conflict
  var newDiv = document.createElement('div');
  for (const [index, char] of Array.from(inputText).entries()) {
    var newSpan = document.createElement('span');
    newSpan.textContent = char;
    newSpan.classList.add('letter-bubble');
    if (targetWord[index] == char)
      newSpan.classList.add('exact-match');
    else if (targetWord.includes(char))
      newSpan.classList.add('letter-match');
    else
      newSpan.classList.add('no-match');
    newDiv.appendChild(newSpan);
  }

  if (inputText == targetWord) {
    confetti();
    updateScore(attemptCount);
    updateWordPerformance(targetWord, attemptCount); // Update performance history
    changeTargetWord();
    newDiv.innerHTML += '✅';  // ✓
  } else {
    attemptCount += 1;
    newDiv.innerHTML += '❌';
  }

  historyDiv.insertBefore(newDiv, historyDiv.firstChild);
  document.getElementById(INPUT_ID).textContent = '';
}

function isLetter(k) {
  if (k.length != 1) {
    return false;
  }
  let n = k.charCodeAt(0);
  return (n >= 65 && n < 91) || (n >= 97 && n < 123);
}

function shuffle(array) {
  let currentIndex = array.length;

  while (currentIndex != 0) {

    let randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex--;

    [array[currentIndex], array[randomIndex]] = [
      array[randomIndex], array[currentIndex]];
  }
}

document.addEventListener('DOMContentLoaded', () => {
  var btnSpeak = document.getElementById('btnSpeak');
  btnSpeak.addEventListener('click', () => {
    document.getElementById(AUDIO_ID).play();
  });

  document.addEventListener('keydown', (event) => {
    if (isLetter(event.key)) {
      tryAddLetter(event.key.toLowerCase());
    } else if (event.key == 'Backspace') {
      tryRemoveLetter();
    } else if (event.key == 'Enter') {
      tryWordDone();
    }
  });

  document.getElementById(AUDIO_ID).addEventListener('canplaythrough', () => {
    document.getElementById(AUDIO_ID).play();
  });

  // Handle tracking checkbox
  const chkTrack = document.getElementById('chkTrack');
  chkTrack.checked = isTrackingEnabled;
  chkTrack.addEventListener('change', () => {
    isTrackingEnabled = chkTrack.checked;
    saveTrackingSetting();
    // If tracking is enabled, re-shuffle/re-select based on weights
    // If tracking is disabled, revert to simple sequential if desired, or keep current word.
    // For now, simply changing the setting doesn't immediately change the target word.
  });


  shuffle(wordList); // Still shuffle for initial sequential access if tracking is off.
  changeTargetWord();
}, {once: true});
