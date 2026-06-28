#!/usr/bin/env python3

import csv
import statistics
from typing import Optional


EVENTS_FILE = "T5/T5-events.csv"
CLIENT_FILE = "T5/T5-HAProxy-client-final.csv"

STABLE_SUCCESS_COUNT = 10


def read_events(filename: str) -> dict[int, dict[str, int]]:
    runs: dict[int, dict[str, int]] = {}

    with open(filename, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            run = int(row["run"])
            event = row["event"]
            timestamp_ns = int(row["timestamp_ns"])

            runs.setdefault(run, {})[event] = timestamp_ns

    return runs


def read_requests(filename: str) -> list[dict]:
    requests = []

    with open(filename, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            requests.append(
                {
                    "request_id": int(row["request_id"]),
                    "start_ns": int(row["start_timestamp_ns"]),
                    "end_ns": int(row["end_timestamp_ns"]),
                    "result": row["result"],
                    "http_code": int(row["http_code"]),
                    "backend": row["backend"],
                }
            )

    return requests


def is_success(request: dict) -> bool:
    return (
        request["result"] == "OK"
        and request["http_code"] == 200
    )


def ns_to_ms(timestamp_ns: int, reference_ns: int) -> float:
    return (timestamp_ns - reference_ns) / 1_000_000


def find_stable_recovery(
    requests: list[dict],
    last_error_end_ns: int,
) -> tuple[Optional[int], Optional[int]]:
    """
    Zwraca:
    1. czas zakończenia pierwszej odpowiedzi z serii stabilnych sukcesów,
    2. czas zakończenia odpowiedzi potwierdzającej serię N sukcesów.
    """

    consecutive_successes = 0
    first_success_end_ns: Optional[int] = None

    for request in sorted(requests, key=lambda item: item["end_ns"]):
        if request["end_ns"] <= last_error_end_ns:
            continue

        if is_success(request):
            if consecutive_successes == 0:
                first_success_end_ns = request["end_ns"]

            consecutive_successes += 1

            if consecutive_successes >= STABLE_SUCCESS_COUNT:
                return first_success_end_ns, request["end_ns"]

        else:
            consecutive_successes = 0
            first_success_end_ns = None

    return None, None


def format_value(value: Optional[float]) -> str:
    if value is None:
        return ""

    return f"{value:.3f}"


events = read_events(EVENTS_FILE)
requests = read_requests(CLIENT_FILE)

recovery_results = []
outage_results = []

print(
    "run,error_count,"
    "first_error_start_ms,"
    "last_error_start_ms,"
    "last_error_end_ms,"
    "stable_recovery_start_ms,"
    "stable_recovery_confirmed_ms,"
    "outage_window_ms"
)

for run, timestamps in sorted(events.items()):
    if "STOP_KEEPALIVED" not in timestamps:
        print(f"{run},ERROR_MISSING_STOP_EVENT")
        continue

    if "START_KEEPALIVED" not in timestamps:
        print(f"{run},ERROR_MISSING_START_EVENT")
        continue

    fault_ns = timestamps["STOP_KEEPALIVED"]
    restore_ns = timestamps["START_KEEPALIVED"]

    # Analizujemy żądania rozpoczęte podczas kontrolowanego
    # okresu awarii, przed przywróceniem węzła A.
    run_requests = [
        request
        for request in requests
        if fault_ns <= request["start_ns"] < restore_ns
    ]

    errors = [
        request
        for request in run_requests
        if not is_success(request)
    ]

    if not errors:
        print(
            f"{run},0,"
            "NO_ERROR,NO_ERROR,NO_ERROR,"
            "NO_ERROR,NO_ERROR,NO_ERROR"
        )
        continue

    first_error = min(
        errors,
        key=lambda request: request["start_ns"],
    )

    last_error_by_start = max(
        errors,
        key=lambda request: request["start_ns"],
    )

    last_error_by_end = max(
        errors,
        key=lambda request: request["end_ns"],
    )

    first_error_start_ms = ns_to_ms(
        first_error["start_ns"],
        fault_ns,
    )

    last_error_start_ms = ns_to_ms(
        last_error_by_start["start_ns"],
        fault_ns,
    )

    last_error_end_ms = ns_to_ms(
        last_error_by_end["end_ns"],
        fault_ns,
    )

    (
        stable_recovery_start_ns,
        stable_recovery_confirmed_ns,
    ) = find_stable_recovery(
        run_requests,
        last_error_by_end["end_ns"],
    )

    if stable_recovery_start_ns is None:
        stable_recovery_start_ms = None
        stable_recovery_confirmed_ms = None
        outage_window_ms = None
    else:
        stable_recovery_start_ms = ns_to_ms(
            stable_recovery_start_ns,
            fault_ns,
        )

        stable_recovery_confirmed_ms = ns_to_ms(
            stable_recovery_confirmed_ns,
            fault_ns,
        )

        outage_window_ms = (
            stable_recovery_start_ns
            - first_error["start_ns"]
        ) / 1_000_000

        recovery_results.append(stable_recovery_start_ms)
        outage_results.append(outage_window_ms)

    print(
        f"{run},"
        f"{len(errors)},"
        f"{first_error_start_ms:.3f},"
        f"{last_error_start_ms:.3f},"
        f"{last_error_end_ms:.3f},"
        f"{format_value(stable_recovery_start_ms)},"
        f"{format_value(stable_recovery_confirmed_ms)},"
        f"{format_value(outage_window_ms)}"
    )


def print_statistics(name: str, values: list[float]) -> None:
    if not values:
        return

    print()
    print(f"{name}_count={len(values)}")
    print(f"{name}_mean_ms={statistics.mean(values):.3f}")
    print(f"{name}_median_ms={statistics.median(values):.3f}")
    print(f"{name}_min_ms={min(values):.3f}")
    print(f"{name}_max_ms={max(values):.3f}")

    if len(values) > 1:
        print(
            f"{name}_stddev_ms="
            f"{statistics.stdev(values):.3f}"
        )


print_statistics("recovery", recovery_results)
print_statistics("outage", outage_results)
