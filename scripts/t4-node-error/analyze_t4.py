#!/usr/bin/env python3

import csv


EVENTS_FILE = "T4/T4-events.csv"
CLIENT_FILE = "T4/T4-HAProxy-client-final.csv"


def read_events(filename):
    runs = {}

    with open(filename, encoding="utf-8") as file:
        next(file)

        for line in file:
            # Data ISO zawiera przecinek, ale pierwsze trzy pola są poprawne.
            fields = line.rstrip().split(",", 3)

            run = int(fields[0])
            event = fields[1]
            timestamp_ns = int(fields[2])

            runs.setdefault(run, {})[event] = timestamp_ns

    return runs


def read_requests(filename):
    requests = []

    with open(filename, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            requests.append(
                {
                    "start_ns": int(row["start_timestamp_ns"]),
                    "end_ns": int(row["end_timestamp_ns"]),
                    "result": row["result"],
                    "backend": row["backend"],
                }
            )

    return requests


events = read_events(EVENTS_FILE)
requests = read_requests(CLIENT_FILE)

print(
    "run,error_count,first_error_start_ms,"
    "last_error_start_ms,last_error_end_ms"
)

for run, timestamps in sorted(events.items()):
    kill_ns = timestamps["KILL"]
    start_ns = timestamps["START"]

    errors = [
        request
        for request in requests
        if request["result"] != "OK"
        and kill_ns <= request["start_ns"] < start_ns
    ]

    if not errors:
        print(f"{run},0,,,")
        continue

    first_error = min(errors, key=lambda request: request["start_ns"])
    last_error_start = max(errors, key=lambda request: request["start_ns"])
    last_error_end = max(errors, key=lambda request: request["end_ns"])

    first_start_ms = (
        first_error["start_ns"] - kill_ns
    ) / 1_000_000

    last_start_ms = (
        last_error_start["start_ns"] - kill_ns
    ) / 1_000_000

    last_end_ms = (
        last_error_end["end_ns"] - kill_ns
    ) / 1_000_000

    print(
        f"{run},"
        f"{len(errors)},"
        f"{first_start_ms:.3f},"
        f"{last_start_ms:.3f},"
        f"{last_end_ms:.3f}"
    )
