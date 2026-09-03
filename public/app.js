const pick = id => {
  const buttons = [...document.querySelectorAll(`#${id} button`)];
  buttons.forEach(button => button.addEventListener('click', () => {
    buttons.forEach(item => item.classList.remove('active'));
    button.classList.add('active');
  }));
  return () => buttons.find(button => button.classList.contains('active'))?.textContent?.trim();
};

const selectedMode = pick('modes');
const selectedDuration = pick('durations');

const secondsFor = duration => duration.startsWith('≤') ? 60 : duration.startsWith('3') ? 300 : 1200;

async function pollJob(jobId, statusEl) {
  for (;;) {
    await new Promise(resolve => setTimeout(resolve, 2500));
    const response = await fetch(`/api/status?id=${encodeURIComponent(jobId)}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'Unable to read job status.');

    if (data.status === 'completed') {
      statusEl.innerHTML = data.output_url
        ? `✅ Video ready — <a href="${data.output_url}" target="_blank" rel="noopener">Open video</a>`
        : '✅ Video rendered. The GPU worker has completed the job.';
      return;
    }
    if (data.status === 'failed') throw new Error(data.error || 'Video generation failed.');
    statusEl.textContent = `⏳ ${data.status || 'processing'}…`;
  }
}

document.querySelector('#generate').addEventListener('click', async () => {
  const prompt = document.querySelector('#prompt').value.trim();
  const status = document.querySelector('#status');
  const voice = document.querySelector('select').value;
  const style = document.querySelectorAll('select')[1].value;
  const duration = selectedDuration();
  const inputType = selectedMode().toLowerCase();

  if (!prompt) {
    status.textContent = 'Please enter an instruction first.';
    return;
  }

  status.textContent = '⏳ Connecting to the remote GPU worker…';
  const payload = {
    prompt,
    duration_seconds: secondsFor(duration),
    language: /amharic/i.test(prompt) ? 'am' : 'en',
    aspect_ratio: '16:9',
    input_type: inputType,
    voice: voice.toLowerCase().replaceAll(' ', '_'),
    style: style.toLowerCase().replaceAll(' ', '_')
  };

  try {
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'Generation could not be started.');
    status.textContent = `✅ Job queued: ${data.job_id}`;
    await pollJob(data.job_id, status);
  } catch (error) {
    status.textContent = `⚠️ ${error.message}`;
  }
});
