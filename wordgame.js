const AUDIO_ID = 'audioSource';
const INPUT_ID = 'divInput';

var nextTargetWordInd = 0;
var targetWord;
var attemptCount;

function setTargetWord(word) {
  console.log('target word: ' + word);
  targetWord = word;
  document.getElementById(AUDIO_ID).src = 'snd/' + word + '.mp3';
  attemptCount = 1;
}

function changeTargetWord() {
  setTargetWord(wordList[nextTargetWordInd]);
  nextTargetWordInd = (nextTargetWordInd + 1) % wordList.length;
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

  var history = document.getElementById('history');
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
    changeTargetWord();
    newDiv.innerHTML += '✅';  // ✓
  } else {
    attemptCount += 1;
    newDiv.innerHTML += '❌';
  }

  history.insertBefore(newDiv, history.firstChild);
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

  shuffle(wordList);
  changeTargetWord();
}, {once: true});
