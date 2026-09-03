const workers = () => (process.env.GPU_WORKER_URLS || process.env.GPU_WORKER_URL || '')
  .split(',').map(x => x.trim().replace(/\/$/, '')).filter(Boolean);

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  const urls = workers();
  if (!urls.length) return res.status(503).json({ error: 'No remote GPU worker is configured.', code: 'GPU_WORKER_NOT_CONFIGURED' });

  let lastError = 'No worker accepted the job.';
  for (const worker of urls) {
    try {
      const response = await fetch(`${worker}/jobs`, {
        method: 'POST',
        headers: { 'content-type': 'application/json', ...(process.env.GPU_WORKER_TOKEN ? { authorization: `Bearer ${process.env.GPU_WORKER_TOKEN}` } : {}) },
        body: JSON.stringify(req.body),
        signal: AbortSignal.timeout(60000)
      });
      const text = await response.text();
      let data;
      try { data = JSON.parse(text); } catch { data = { raw: text }; }
      if (response.ok) return res.status(response.status).json({ ...data, routed: 'remote-gpu' });
      lastError = data.error || `Worker returned HTTP ${response.status}`;
    } catch (error) { lastError = error.message || lastError; }
  }
  return res.status(502).json({ error: 'All configured remote GPU workers are unavailable.', detail: lastError, code: 'GPU_WORKERS_UNAVAILABLE' });
}
