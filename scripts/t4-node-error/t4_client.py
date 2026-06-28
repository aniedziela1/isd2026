#!/usr/bin/env python3

import argparse
import csv
import re
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor


H1_PATTERN = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
write_lock = threading.Lock()


def send_request(url: str, timeout: float, request_id: int, writer, output_file):
    start_ns = time.time_ns()
    start_iso = time.strftime(
        "%Y-%m-%dT%H:%M:%S",
        time.localtime(start_ns / 1_000_000_000),
    )

    http_code = 0
    backend = ""
    result = "ERROR"
    error_message = ""

    try:
        request = urllib.request.Request(
            url,
            headers={"Connection": "close"},
        )

        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            http_code = response.status

        match = H1_PATTERN.search(body)

        if match:
            backend = re.sub(r"\s+", " ", match.group(1)).strip()

        result = "OK" if http_code == 200 else "HTTP_ERROR"

    except urllib.error.HTTPError as error:
        http_code = error.code
        result = "HTTP_ERROR"
        error_message = str(error)

    except Exception as error:
        result = "ERROR"
        error_message = str(error)

    end_ns = time.time_ns()
    latency_ms = (end_ns - start_ns) / 1_000_000

    with write_lock:
        writer.writerow(
            [
                request_id,
                start_ns,
                end_ns,
                start_iso,
                http_code,
                f"{latency_ms:.3f}",
                backend,
                result,
                error_message,
            ]
        )
        output_file.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vip", required=True)
    parser.add_argument("--rate", type=float, default=10)
    parser.add_argument("--duration", type=float, default=300)
    parser.add_argument("--timeout", type=float, default=2)
    parser.add_argument("--workers", type=int, default=30)
    parser.add_argument("--output", default="T4-client.csv")
    args = parser.parse_args()

    url = f"http://[{args.vip}]/"
    interval = 1.0 / args.rate
    end_time = time.monotonic() + args.duration

    with open(args.output, "w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)

        writer.writerow(
            [
                "request_id",
                "start_timestamp_ns",
                "end_timestamp_ns",
                "start_time",
                "http_code",
                "latency_ms",
                "backend",
                "result",
                "error",
            ]
        )

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            request_id = 0
            next_request = time.monotonic()

            while time.monotonic() < end_time:
                request_id += 1

                executor.submit(
                    send_request,
                    url,
                    args.timeout,
                    request_id,
                    writer,
                    output_file,
                )

                next_request += interval
                sleep_time = next_request - time.monotonic()

                if sleep_time > 0:
                    time.sleep(sleep_time)

    print(f"Zakończono. Wyniki: {args.output}")


if __name__ == "__main__":
    main()
