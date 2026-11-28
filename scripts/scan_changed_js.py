import json
import os
import subprocess
import sys
import time
import tempfile
from pathlib import Path

VALIDATOR = Path(__file__).with_name("check_scan_result.py")

MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2
MAX_RETRY_DELAY = 30

RETRYABLE_HTTP_CODES = (502, 503, 504)
RETRYABLE_CURL_CODES = (6, 7, 28, 52, 55, 56)


def get_retry_after(headers):
    """Extract Retry-After from the final HTTP response."""

    retry_after = None

    for line in headers.splitlines():
        if line.startswith("HTTP/"):
            retry_after = None
        elif line.lower().startswith("retry-after:"):
            retry_after = line.split(":", 1)[1].strip()

    if retry_after is None:
        return DEFAULT_RETRY_DELAY

    if not retry_after.isascii() or not retry_after.isdecimal():
        sys.exit("Scan incomplete: unsupported Retry-After header.")

    delay = int(retry_after)

    if delay > MAX_RETRY_DELAY:
        sys.exit("Scan incomplete: Retry-After exceeds retry budget.")

    return max(DEFAULT_RETRY_DELAY, delay)


def request_scan(curl_command, payload, filename):
    """Submit a scan request with bounded retries."""

    for attempt in range(MAX_RETRIES + 1):
        delay = DEFAULT_RETRY_DELAY

        print(
            f"Scanner request attempt {attempt + 1}/{MAX_RETRIES + 1}.",
            flush=True
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            header_path = Path(temp_dir) / "headers.txt"

            command = curl_command + [
                "--dump-header", str(header_path),
                "--write-out", "\n%{http_code}"
            ]

            try:
                response = subprocess.run(
                    command,
                    input=payload,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=20,
                )

            except subprocess.TimeoutExpired:
                reason = "Python subprocess timeout"
                retryable = True

            else:
                body, separator, status = response.stdout.rpartition(b"\n")

                http_status = (
                    int(status)
                    if separator and len(status) == 3 and status.isdigit()
                    else 0
                )

                if response.returncode == 0 and http_status == 200:
                    return body

                if http_status == 413:
                    sys.exit(
                        f"Scan incomplete: file too large to scan: {filename!r}."
                    )

                if http_status in RETRYABLE_HTTP_CODES:
                    reason = f"HTTP {http_status}"
                    retryable = True

                    if header_path.is_file() and attempt < MAX_RETRIES:
                        delay = get_retry_after(
                            header_path.read_text(errors="replace")
                        )

                elif (
                    http_status in (0, 200)
                    and response.returncode in RETRYABLE_CURL_CODES
                ):
                    reason = f"curl exit code {response.returncode}"
                    retryable = True

                else:
                    reason = (
                        f"HTTP {http_status}"
                        if http_status and http_status != 200
                        else f"curl exit code {response.returncode}"
                    )
                    retryable = False

        if not retryable:
            sys.exit(
                f"Scan incomplete: {reason} for {filename!r}."
            )

        if attempt == MAX_RETRIES:
            sys.exit(
                f"Scan incomplete: {reason} for {filename!r}. "
                "Retry attempts exhausted."
            )

        print(
            f"Scanner request failed ({reason}). "
            f"Retry {attempt + 1}/{MAX_RETRIES} "
            f"in {delay} seconds.",
            flush=True
        )

        time.sleep(delay)


def main():
    if len(sys.argv) != 3:
        sys.exit(
            "Usage: python3 scripts/scan_changed_js.py BASE_SHA HEAD_SHA"
        )

    base, head = sys.argv[1:]
    revision_range = f"{base}...{head}"

    paths = subprocess.check_output([
        "git", "diff", "--name-only", "-z", "--no-renames",
        "--diff-filter=AMT", revision_range, "--", "*.js",
    ])

    files = [
        os.fsdecode(path)
        for path in paths.split(b"\0")
        if path
    ]

    if not files:
        print("No changed JavaScript files to scan.")
        return 0

    url = os.environ.get("SCANNER_URL", "").rstrip("/")
    key = os.environ.get("SCANNER_API_KEY")

    if not url or not key:
        sys.exit(
            "Scan incomplete: scanner URL or API key is missing."
        )

    for filename in files:
        print(f"Scanning {filename!r}", flush=True)

        code = subprocess.check_output(
            ["git", "show", f"{head}:{filename}"]
        ).decode("utf-8")

        payload = json.dumps({
            "filename": filename,
            "code": code
        }).encode()

        curl_command = [
            "curl",
            "--silent",
            "--show-error",
            "--connect-timeout", "5",
            "--max-time", "15",
        ]

        if url.startswith("https://"):
            certificate = os.environ.get(
                "SCANNER_CA_CERT",
                "certs/alb-cert.pem"
            )

            if not Path(certificate).is_file():
                sys.exit(
                    "Scan incomplete: scanner certificate is missing."
                )

            curl_command.extend([
                "--proto", "=https",
                "--cacert", certificate,
            ])

        elif url != "http://127.0.0.1:3001":
            sys.exit(
                "Scan incomplete: HTTPS is required for remote scanners."
            )

        curl_command.extend([
            "-H", "Content-Type: application/json",
            "-H", f"x-api-key: {key}",
            "--data-binary", "@-",
            f"{url}/scan/code",
        ])

        body = request_scan(curl_command, payload, filename)

        try:
            report = json.loads(body)
        except (ValueError, UnicodeError):
            sys.exit("Scan incomplete: invalid JSON response.")

        if not isinstance(report, dict) or report.get("success") is not True:
            sys.exit("Scan incomplete: unsuccessful scanner response.")

        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            input=body
        )

        if result.returncode:
            return 1

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())

    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        UnicodeError,
        OSError,
    ):
        sys.exit("Scan incomplete: scanner client execution failed.")
