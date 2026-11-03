import os, json, urllib.request, boto3

cw = boto3.client("cloudwatch")
URL = os.environ["SCANNER_URL"]

def lambda_handler(event, context):
    healthy, detail = 0, ""
    try:
        with urllib.request.urlopen(URL, timeout=10) as r:
            healthy = 1 if r.status == 200 else 0
            detail = f"status {r.status}"
    except Exception as e:
        detail = f"{type(e).__name__}: {e}"

    print(json.dumps({"healthy": healthy, "detail": detail, "url": URL}))
    cw.put_metric_data(
        Namespace="SecureGate",
        MetricData=[{"MetricName": "ScannerHealthy", "Value": healthy, "Unit": "None"}],
    )
    return {"healthy": healthy, "detail": detail}
