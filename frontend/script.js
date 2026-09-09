const urlInput = document.getElementById('youtubeUrl');
const summarizeBtn = document.getElementById('summarizeBtn');
const loading = document.getElementById('loading');
const result = document.getElementById('result');
const errorBox = document.getElementById('errorBox');

const summaryText = document.getElementById('summaryText');
const keyPointsList = document.getElementById('keyPointsList');
const importantConceptsList = document.getElementById('importantConceptsList');
const takeawayText = document.getElementById('takeawayText');

function showLoading(show) {
  loading.classList.toggle('hidden', !show);
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove('hidden');
}

function hideError() {
  errorBox.textContent = '';
  errorBox.classList.add('hidden');
}

function renderResult(data) {
  summaryText.textContent = data.summary || '';
  takeawayText.textContent = data.takeaway || '';

  keyPointsList.innerHTML = '';
  (data.key_points || []).forEach((point) => {
    const li = document.createElement('li');
    li.textContent = point;
    keyPointsList.appendChild(li);
  });

  importantConceptsList.innerHTML = '';
  (data.important_concepts || []).forEach((concept) => {
    const li = document.createElement('li');
    li.textContent = concept;
    importantConceptsList.appendChild(li);
  });

  result.classList.remove('hidden');
}

async function summarizeVideo() {
  const youtubeUrl = urlInput.value.trim();

  if (!youtubeUrl) {
    showError('Please enter a YouTube URL.');
    return;
  }

  hideError();
  showLoading(true);
  result.classList.add('hidden');

  try {
    const response = await fetch('http://127.0.0.1:8000/summarize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ youtube_url: youtubeUrl }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Something went wrong.');
    }

    renderResult(data);
  } catch (error) {
    showError(error.message || 'Unable to summarize the video.');
  } finally {
    showLoading(false);
  }
}

summarizeBtn.addEventListener('click', summarizeVideo);
urlInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    summarizeVideo();
  }
});
