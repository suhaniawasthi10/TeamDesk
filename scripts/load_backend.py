"""Send bounded, read-only employee requests for the HPA demonstration."""

import argparse
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--seconds", type=int, default=180)
    parser.add_argument("--rate", type=int, default=120)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 300 or not 1 <= args.rate <= 200:
        parser.error("Use 1–300 seconds and 1–200 requests per second.")

    workers = min(8, args.rate)
    interval = workers / args.rate
    deadline = time.monotonic() + args.seconds
    stop = threading.Event()

    def worker():
        success = errors = 0
        while time.monotonic() < deadline and not stop.is_set():
            start = time.monotonic()
            try:
                with urlopen(args.url, timeout=5) as response:
                    response.read()
                    if response.status != 200:
                        raise ValueError("Non-200 response")
                success += 1
            except (HTTPError, URLError, TimeoutError, ValueError):
                errors += 1
                if errors >= 5:
                    stop.set()
            stop.wait(max(0, interval - (time.monotonic() - start)))
        return success, errors

    started = time.monotonic()
    print(
        f"Read-only load: at most {args.rate} requests/s for {args.seconds}s.",
        flush=True,
    )
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda _: worker(), range(workers)))
    success = sum(x[0] for x in results)
    errors = sum(x[1] for x in results)
    elapsed = time.monotonic() - started
    print(
        f"Completed {success} successful GET requests; {errors} errors; {elapsed:.1f}s."
    )
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
