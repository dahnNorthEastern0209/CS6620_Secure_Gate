import json
import os
import subprocess
import sys
import time
from pathlib import Path

VALIDATOR = Path(__file__).with_name("check_scan_result.py")


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python3 scripts/scan_changed_js.py BASE_SHA HEAD_SHA")

    base, head = sys.argv[1:]
    revision_range = f"{base}...{head}"

    paths = subprocess.check_output([
        "git", "diff", "--name-only", "-z", "--no-renames",
        "--diff-filter=AMT", revision_range, "--", "*.js",
    ])
    files = [os.fsdecode(path) for path in paths.split(b"\0") if path]

    if not files:
        print("No changed JavaScript files to scan.")
        return 0

    url = os.environ.get("SCANNER_URL", "").rstrip("/")
    key = os.environ.get("SCANNER_API_KEY")
    if not url or not key:
        sys.exit("Scan incomplete: scanner URL or API key is missing.")

    for filename in files:
        print(f"Scanning {filename!r}", flush=True)
        code = subprocess.check_output(
            ["git", "show", f"{head}:{filename}"]
        ).decode("utf-8")
        payload = json.dumps({"filename": filename, "code": code}).encode()

        curl_command = [
            "curl",
            "--fail",
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

        curl_command.extend([
            "-H", "Content-Type: application/json",
            "-H", f"x-api-key: {key}",
            "--data-binary", "@-",
            f"{url}/scan/code",
        ])

        for attempt in range(4):
            response = subprocess.run(
                curl_command,
                input=payload,
                stdout=subprocess.PIPE,
                timeout=20,
            )

            if response.returncode == 0:
                break

            if response.returncode not in (6, 7, 28, 52, 55, 56):
                break

            if attempt < 3:
                print(
                    f"Scanner request failed. Retry {attempt + 1}/3.",
                    flush=True,
                )
                time.sleep(2)


        if response.returncode:
            sys.exit(f"Scan incomplete: scanner request failed for {filename!r}.")

        result = subprocess.run(
            [sys.executable, str(VALIDATOR)], input=response.stdout
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
    ) as error:
        sys.exit(f"Scan incomplete: {error}")