#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import statistics
import time

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="Repeatable, bounded pilot load profile")
    parser.add_argument("--base-url", default="http://localhost:8000"); parser.add_argument("--path", default="/health")
    parser.add_argument("--requests", type=int, default=100); parser.add_argument("--concurrency", type=int, default=4); args = parser.parse_args()
    def request(_):
        started = time.perf_counter(); response = httpx.get(args.base_url + args.path, timeout=30); return time.perf_counter() - started, response.status_code
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool: results = list(pool.map(request, range(args.requests)))
    latencies = sorted(item[0] * 1000 for item in results); errors = sum(1 for _, status in results if status >= 400)
    p95 = latencies[min(len(latencies) - 1, int(len(latencies) * .95))]
    print(f"requests={len(results)} concurrency={args.concurrency} p50_ms={statistics.median(latencies):.2f} p95_ms={p95:.2f} errors={errors}")
    return 1 if errors else 0


if __name__ == "__main__": raise SystemExit(main())
