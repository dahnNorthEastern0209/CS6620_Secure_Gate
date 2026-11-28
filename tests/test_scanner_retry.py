
import subprocess
import sys
import unittest

from pathlib import Path
from unittest.mock import patch, call

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "scripts")
)

import scan_changed_js as scanner


class TestScannerRetry(unittest.TestCase):

    def setUp(self):
        self.command = ["curl", "https://example.invalid/scan/code"]
        self.payload = b'{"code": "const answer = 42;"}'
        self.filename = "sample.js"

    def response(self, status, body=b"{}", returncode=0):
        return subprocess.CompletedProcess(
            args=self.command,
            returncode=returncode,
            stdout=body + b"\n" + str(status).zfill(3).encode(),
            stderr=b"",
        )

    @patch("scan_changed_js.time.sleep")
    @patch("scan_changed_js.subprocess.run")
    def test_http_200(self, mock_run, mock_sleep):
        mock_run.return_value = self.response(
            200, b'{"success": true}'
        )

        body = scanner.request_scan(
            self.command, self.payload, self.filename
        )

        self.assertEqual(body, b'{"success": true}')
        self.assertEqual(mock_run.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("scan_changed_js.time.sleep")
    @patch("scan_changed_js.subprocess.run")
    def test_http_503_then_success(self, mock_run, mock_sleep):
        mock_run.side_effect = [
            self.response(503),
            self.response(200, b'{"success": true}'),
        ]

        body = scanner.request_scan(
            self.command, self.payload, self.filename
        )

        self.assertEqual(body, b'{"success": true}')
        self.assertEqual(mock_run.call_count, 2)
        mock_sleep.assert_called_once_with(2)

    @patch("scan_changed_js.time.sleep")
    @patch("scan_changed_js.subprocess.run")
    def test_retry_after_10(self, mock_run, mock_sleep):

        def fake_request(command, **kwargs):
            header_path = Path(
                command[command.index("--dump-header") + 1]
            )

            if mock_run.call_count == 1:
                header_path.write_text(
                    "HTTP/1.1 503 Service Unavailable\n"
                    "Retry-After: 10\n\n"
                )
                return self.response(503)

            return self.response(200, b'{"success": true}')

        mock_run.side_effect = fake_request

        body = scanner.request_scan(
            self.command, self.payload, self.filename
        )

        self.assertEqual(body, b'{"success": true}')
        self.assertEqual(mock_run.call_count, 2)
        mock_sleep.assert_called_once_with(10)

    @patch("scan_changed_js.time.sleep")
    @patch("scan_changed_js.subprocess.run")
    def test_http_503_retry_exhaustion(self, mock_run, mock_sleep):
        mock_run.return_value = self.response(503)

        with self.assertRaises(SystemExit) as error:
            scanner.request_scan(
                self.command, self.payload, self.filename
            )

        self.assertIn(
            "Retry attempts exhausted",
            str(error.exception)
        )
        self.assertEqual(mock_run.call_count, 4)
        self.assertEqual(mock_sleep.call_count, 3)
        mock_sleep.assert_has_calls([call(2), call(2), call(2)])

    @patch("scan_changed_js.time.sleep")
    @patch("scan_changed_js.subprocess.run")
    def test_http_401_no_retry(self, mock_run, mock_sleep):
        mock_run.return_value = self.response(401)

        with self.assertRaises(SystemExit) as error:
            scanner.request_scan(
                self.command, self.payload, self.filename
            )

        self.assertIn("HTTP 401", str(error.exception))
        self.assertEqual(mock_run.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("scan_changed_js.time.sleep")
    @patch("scan_changed_js.subprocess.run")
    def test_http_413_no_retry(self, mock_run, mock_sleep):
        mock_run.return_value = self.response(413)

        with self.assertRaises(SystemExit) as error:
            scanner.request_scan(
                self.command, self.payload, self.filename
            )

        self.assertIn(
            "file too large",
            str(error.exception)
        )
        self.assertEqual(mock_run.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("scan_changed_js.time.sleep")
    @patch("scan_changed_js.subprocess.run")
    def test_subprocess_timeout(self, mock_run, mock_sleep):
        mock_run.side_effect = [
            subprocess.TimeoutExpired(self.command, 20),
            self.response(200, b'{"success": true}'),
        ]

        body = scanner.request_scan(
            self.command, self.payload, self.filename
        )

        self.assertEqual(body, b'{"success": true}')
        self.assertEqual(mock_run.call_count, 2)
        mock_sleep.assert_called_once_with(2)

    @patch("scan_changed_js.time.sleep")
    @patch("scan_changed_js.subprocess.run")
    def test_tls_error_no_retry(self, mock_run, mock_sleep):
        mock_run.return_value = self.response(
            0, b"", returncode=60
        )

        with self.assertRaises(SystemExit) as error:
            scanner.request_scan(
                self.command, self.payload, self.filename
            )

        self.assertIn(
            "curl exit code 60",
            str(error.exception)
        )
        self.assertEqual(mock_run.call_count, 1)
        mock_sleep.assert_not_called()

    def test_retry_after_exceeds_budget(self):
        with self.assertRaises(SystemExit):
            scanner.get_retry_after(
                "HTTP/1.1 503 Service Unavailable\n"
                "Retry-After: 120\n"
            )

    def test_invalid_retry_after(self):
        with self.assertRaises(SystemExit):
            scanner.get_retry_after(
                "HTTP/1.1 503 Service Unavailable\n"
                "Retry-After: invalid\n"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
