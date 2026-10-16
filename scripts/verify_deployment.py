"""Check that the Ingress serves the intended release and a usable frontend."""

import argparse
import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--url", required=True)
parser.add_argument("--sha", required=True)
args = parser.parse_args()
base = args.url.rstrip("/")

for attempt in range(12):
    try:
        with urlopen(base + "/health", timeout=10) as response:
            health = json.load(response)
        assert health["status"] == "ok" and health["version"] == args.sha
        with urlopen(base + "/ready", timeout=10) as response:
            assert response.status == 200
        with urlopen(base, timeout=10) as response:
            html = response.read().decode()
            assert 'id="root"' in html and "/assets/" in html
        print(
            f"Ingress serves release {args.sha}; readiness and frontend checks passed."
        )
        break
    except (HTTPError, URLError, TimeoutError, AssertionError, ValueError, KeyError):
        if attempt == 11:
            raise SystemExit(
                "Ingress did not serve the expected healthy release in time."
            )
        time.sleep(5)
