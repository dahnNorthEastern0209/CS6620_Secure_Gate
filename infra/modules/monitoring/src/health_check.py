import json, os, ssl, urllib.request
import boto3

ssm = boto3.client("ssm")
cw = boto3.client("cloudwatch")

URL_PARAM  = os.environ.get("SCANNER_URL_PARAM", "/securegate/scanner-url")
CERT_PARAM = os.environ.get("SCANNER_CERT_PARAM", "/securegate/alb-cert")
NAMESPACE  = os.environ.get("METRIC_NAMESPACE", "SecureGate")
CERT_PATH  = "/tmp/alb-cert.pem"


def _param(name):
    return ssm.get_parameter(Name=name)["Parameter"]["Value"]


def _ssl_context():
    """Trust the ALB's self-signed certificate.

    The certificate is re-read on every invocation and rewritten only when it
    has changed, so a rotated certificate takes effect on the next run without
    a redeploy. Caching on cold start alone left warm containers verifying
    against a stale file in /tmp.
    """
    if not CERT_PARAM:
        return None

    cert = _param(CERT_PARAM)
    existing = ""
    if os.path.exists(CERT_PATH):
        with open(CERT_PATH) as fh:
            existing = fh.read()
    if existing != cert:
        with open(CERT_PATH, "w") as fh:
            fh.write(cert)

    ctx = ssl.create_default_context(cafile=CERT_PATH)
    # The self-signed certificate does not carry the ALB's DNS name.
    # The chain is still verified; only the hostname match is skipped.
    ctx.check_hostname = False
    return ctx


def lambda_handler(event, context):
    base = _param(URL_PARAM).rstrip("/")
    url = base if base.endswith("/health") else f"{base}/health"

    healthy, detail = 0, ""
    try:
        ctx = _ssl_context()
        with urllib.request.urlopen(url, timeout=10, context=ctx) as resp:
            healthy = 1 if resp.status == 200 else 0
            detail = f"status {resp.status}"
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"

    cw.put_metric_data(
        Namespace=NAMESPACE,
        MetricData=[{"MetricName": "ScannerHealthy", "Value": healthy, "Unit": "None"}],
    )

    result = {"healthy": healthy, "detail": detail, "url": url}
    print(json.dumps(result))
    return result
