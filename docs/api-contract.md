# SecureGate Scanner API Contract

Draft for team review. Based on the course-provided SAST scanner (`scanner/`).

## Scan code

`POST /scan/code`

**Headers**

| Header | Value |
|---|---|
| `Content-Type` | `application/json` |
| `x-api-key` | Shared API key (stored in GitHub Secrets and Parameter Store) |

**Request body**

```json
{
  "code": "<file contents>",
  "filename": "src/app.js"
}
```

- One request per changed JavaScript file.
- Always send `filename`; otherwise findings are reported as `untitled.js`.
- Maximum request size: 1 MB.

**Response (200)**

```json
{
  "success": true,
  "filename": "src/app.js",
  "scannedAt": "2026-10-31T06:33:55.814Z",
  "summary": { "totalVulnerabilities": 1, "high": 1, "medium": 0, "low": 0 },
  "vulnerabilities": [
    {
      "id": "HARDCODED_SECRET",
      "name": "Hardcoded Secret",
      "severity": "HIGH",
      "description": "Hardcoded password",
      "message": "Hardcoded secret detected. Move secrets to environment variables.",
      "file": "src/app.js",
      "line": 1,
      "column": 7,
      "evidence": "const password = \"admin123\";"
    }
  ]
}
```

## Error responses

| Code | Meaning | What GitHub Actions does |
|---|---|---|
| `401` | Missing or wrong API key | Fail immediately (configuration error) |
| `413` | Request larger than 1 MB | Fail with "file too large to scan" |
| `503` | Scanner busy (more than 5 scans in progress); includes `Retry-After` | Retry (up to 3 times) |

## Pass/fail rule (GitHub Actions)

1. Any file with `summary.high > 0` → **check fails** (security finding).
2. HTTP error, timeout (60 s per request), or `success` not `true` after retries → **check fails** as "scanner unavailable".
3. Otherwise → **check passes**. Medium and low findings are shown in the log but do not block.

## Health check

`GET /health` (no API key required)

```json
{ "status": "healthy", "service": "SAST Scanner", "version": "1.0.0", "timestamp": "..." }
```

Used by the Lambda health check and the load balancer target check.

## Notes

- The provided scanner checks **JavaScript** only. Python scanning with Semgrep is planned as an extension.
- The scanner URL is provided to GitHub Actions as a repository variable (`SCANNER_URL`), set from Terraform output.
