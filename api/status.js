const workers = () => (process.env.GPU_WORKER_URLS || process.env.GPU_WORKER_URL || '')
  .split(',').map(x => x.trim().replace(/\/$/, '')).filter(Boolean);

export default async function handler(req, res) {
  const jobId = req.query?.id;
  if (!jobId) return res.status(400).json({ error: 'Missing job id' });
  const urls = workers();
  if (!urls.length) return res.status(503).json({ error: 'No remote GPU worker is configured.', code: 'GPU_WORKER_NOT_CONFIGURED' });

  let lastError = 'Job not found on configured workers.';
  for (const worker of urls) {
    try {
      const response = await fetch(`${worker}/jobs/${encodeURIComponent(jobId)}`, {
        headers: process.env.GPU_WORKER_TOKEN ? { authorization: `Bearer ${process.env.GPU_WORKER_TOKEN}` } : {},
        signal: AbortSignal.timeout(30000)
      });
      const text = await response.text();
      let data;
      try { data = JSON.parse(text); } catch { data = { raw: text }; }
      if (response.ok) return res.status(response.status).json(data);
      lastError = data.error || `Worker returned HTTP ${response.status}`;
    } catch (error) { lastError = error.message || lastError; }
  }
  return res.status(404).json({ error: lastError, code: 'JOB_NOT_FOUND' });
}
