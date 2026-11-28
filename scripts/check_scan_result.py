import json
import sys

try:
    result = json.load(sys.stdin)
    high = result["summary"]["high"]
    if result["success"] is not True or type(high) is not int or high < 0:
        raise ValueError
except (ValueError, KeyError, TypeError):
    sys.exit("Scan incomplete: invalid or unsuccessful scanner response.")

if high > 0:
    sys.exit(f"Security check failed: {high} HIGH finding(s).")

print("Security check passed: 0 HIGH findings.")