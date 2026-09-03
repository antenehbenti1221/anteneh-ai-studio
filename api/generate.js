export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const worker = process.env.GPU_WORKER_URL;
  const token = process.env.GPU_WORKER_TOKEN;
  if (!worker) {
    return res.status(503).json({
      error: 'Remote GPU worker is not connected yet.',
      code: 'GPU_WORKER_NOT_CONFIGURED'
    });
  }

  try {
    const response = await fetch(`${worker.replace(/\/$/, '')}/jobs`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        ...(token ? { authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify(req.body)
    });
    const text = await response.text();
    let data;
    try { data = JSON.parse(text); } catch { data = { raw: text }; }
    return res.status(response.status).json(data);
  } catch (error) {
    return res.status(502).json({ error: 'Could not reach the remote GPU worker.', detail: error.message });
  }
}
