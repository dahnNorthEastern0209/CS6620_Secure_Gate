// SecureGate scanner guards: request size errors, API key check, scan concurrency cap.
import crypto from 'crypto';

const MAX_CONCURRENT_SCANS = parseInt(process.env.MAX_CONCURRENT_SCANS ?? '5', 10);
let inFlight = 0;

// Turns body-parser errors (e.g. body over the size limit) into JSON responses.
function jsonErrorHandler(err, req, res, next) {
  if (err.type === 'entity.too.large') {
    return res.status(413).json({ success: false, error: 'Request too large (max 1 MB)' });
  }
  if (err.type === 'entity.parse.failed') {
    return res.status(400).json({ success: false, error: 'Invalid JSON body' });
  }
  next(err);
}

// Requires a matching x-api-key header on every route except GET /health.
function apiKeyAuth(req, res, next) {
  if (req.method === 'GET' && req.path === '/health') return next();

  const expected = process.env.SCANNER_API_KEY;
  if (!expected) {
    return res.status(500).json({ success: false, error: 'Scanner API key not configured' });
  }
  const provided = req.get('x-api-key') || '';
  const a = Buffer.from(provided);
  const b = Buffer.from(expected);
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) {
    return res.status(401).json({ success: false, error: 'Unauthorized' });
  }
  next();
}

// Limits how many scan requests run at once; extra requests get 503 + Retry-After.
function concurrencyLimit(req, res, next) {
  if (!req.path.startsWith('/scan')) return next();

  if (inFlight >= MAX_CONCURRENT_SCANS) {
    res.set('Retry-After', '10');
    return res.status(503).json({ success: false, error: 'Scanner busy, retry later' });
  }
  inFlight++;
  let released = false;
  const release = () => { if (!released) { released = true; inFlight--; } };
  res.on('finish', release);
  res.on('close', release);
  next();
}

export { jsonErrorHandler, apiKeyAuth, concurrencyLimit };
