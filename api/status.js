export default async function handler(req, res) {
  const jobId = req.query?.id;
  if (!jobId) return res.status(400).json({ error: 'Missing job id' });

  const worker = process.env.GPU_WORKER_URL;
  const token = process.env.GPU_WORKER_TOKEN;
  if (!worker) return res.status(503).json({ error: 'Remote GPU worker is not connected yet.', code: 'GPU_WORKER_NOT_CONFIGURED' });

  try {
    const response = await fetch(`${worker.replace(/\/$/, '')}/jobs/${encodeURIComponent(jobId)}`, {
      headers: token ? { authorization: `Bearer ${token}` } : {}
    });
    const text = await response.text();
    let data;
    try { data = JSON.parse(text); } catch { data = { raw: text }; }
    return res.status(response.status).json(data);
  } catch (error) {
    return res.status(502).json({ error: 'Could not reach the remote GPU worker.', detail: error.message });
  }
}
