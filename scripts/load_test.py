#!/usr/bin/env python3
"""Load testing script for Collections Sharing feature.

This script performs comprehensive load testing including:
- Collections endpoint with 100+ items
- Public share pages with caching
- Share creation under load
- Database connection pool monitoring

Run with: poetry run python scripts/load_test.py
"""

from __future__ import annotations

import asyncio
import json
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Configuration
API_BASE_URL = "http://localhost:8000/api"
TEST_RESULTS_DIR = Path("docs/testing")


@dataclass
class LoadTestResult:
    """Load test result."""

    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    duration_seconds: float
    requests_per_second: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    avg_ms: float
    errors: list[str]


class LoadTest:
    """Load testing runner for Collections Sharing."""

    def __init__(self, api_url: str = API_BASE_URL):
        """Initialize load test.

        Args:
            api_url: Base URL for API
        """
        self.api_url = api_url
        self.results: list[LoadTestResult] = []

    async def run_all_tests(self) -> dict[str, Any]:
        """Run all load tests.

        Returns:
            Summary of test results
        """
        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.CYAN}LOAD TESTING - Collections Sharing Feature")
        print(f"{Fore.CYAN}{'=' * 80}\n")

        # Run test suites
        await self.test_collections_endpoint()
        await self.test_public_share_pages()
        await self.test_share_creation()
        await self.test_database_connections()

        # Generate summary
        summary = self._generate_summary()

        # Print results
        self._print_results()

        # Save report
        await self._save_report(summary)

        return summary

    # ==================== Collections Endpoint Load Test ====================

    async def test_collections_endpoint(self) -> None:
        """Test collections endpoint with 100+ items.

        Target: p95 < 200ms with 100 concurrent users
        """
        print(f"{Fore.YELLOW}[TEST SUITE] Collections Endpoint Load Test{Style.RESET_ALL}")

        # Step 1: Seed test data (create collection with 100+ items)
        print(f"  {Fore.CYAN}Seeding test data (collection with 100+ items)...{Style.RESET_ALL}")
        collection_id = await self._create_test_collection_with_items(100)

        if not collection_id:
            print(f"  {Fore.RED}Failed to create test collection{Style.RESET_ALL}")
            return

        print(f"  {Fore.GREEN}Created collection {collection_id} with 100 items{Style.RESET_ALL}")

        # Step 2: Run load test (100 concurrent users)
        print(f"  {Fore.CYAN}Running load test (100 concurrent users)...{Style.RESET_ALL}")

        async def fetch_collection():
            """Fetch collection with timing."""
            async with httpx.AsyncClient(base_url=self.api_url, timeout=30.0) as client:
                start = time.perf_counter()
                response = await client.get(f"/v1/collections/{collection_id}")
                duration = (time.perf_counter() - start) * 1000  # Convert to ms
                return {
                    "success": response.status_code == 200,
                    "duration_ms": duration,
                    "status": response.status_code,
                }

        # Run concurrent requests
        start_time = time.perf_counter()
        results = await asyncio.gather(*[fetch_collection() for _ in range(100)], return_exceptions=True)
        total_duration = time.perf_counter() - start_time

        # Process results
        successes = [r for r in results if isinstance(r, dict) and r["success"]]
        failures = [r for r in results if not isinstance(r, dict) or not r.get("success")]
        durations = [r["duration_ms"] for r in successes]

        # Calculate percentiles
        p50 = statistics.median(durations) if durations else 0
        p95 = self._percentile(durations, 95) if durations else 0
        p99 = self._percentile(durations, 99) if durations else 0

        # Store result
        result = LoadTestResult(
            test_name="Collections Endpoint (100 items, 100 concurrent users)",
            total_requests=len(results),
            successful_requests=len(successes),
            failed_requests=len(failures),
            duration_seconds=total_duration,
            requests_per_second=len(results) / total_duration if total_duration > 0 else 0,
            p50_ms=p50,
            p95_ms=p95,
            p99_ms=p99,
            min_ms=min(durations) if durations else 0,
            max_ms=max(durations) if durations else 0,
            avg_ms=statistics.mean(durations) if durations else 0,
            errors=[str(f) for f in failures],
        )
        self.results.append(result)

        # Print result
        self._print_test_result(result, target_p95=200)

    # ==================== Public Share Pages Load Test ====================

    async def test_public_share_pages(self) -> None:
        """Test public share pages with caching.

        Target: p95 < 1s uncached, p95 < 50ms cached
        """
        print(f"\n{Fore.YELLOW}[TEST SUITE] Public Share Pages Load Test{Style.RESET_ALL}")

        # Step 1: Create test share
        print(f"  {Fore.CYAN}Creating test share...{Style.RESET_ALL}")
        share_token, listing_id = await self._create_test_share()

        if not share_token:
            print(f"  {Fore.RED}Failed to create test share{Style.RESET_ALL}")
            return

        print(f"  {Fore.GREEN}Created share: /v1/deals/{listing_id}/{share_token[:8]}...{Style.RESET_ALL}")

        # Step 2: Test uncached requests (500 concurrent)
        print(f"  {Fore.CYAN}Testing uncached requests (500 concurrent)...{Style.RESET_ALL}")

        async def fetch_share(use_cache: bool = True):
            """Fetch share page with timing."""
            async with httpx.AsyncClient(base_url=self.api_url, timeout=30.0) as client:
                start = time.perf_counter()
                headers = {} if use_cache else {"Cache-Control": "no-cache"}
                response = await client.get(
                    f"/v1/deals/{listing_id}/{share_token}",
                    headers=headers
                )
                duration = (time.perf_counter() - start) * 1000
                return {
                    "success": response.status_code == 200,
                    "duration_ms": duration,
                    "status": response.status_code,
                }

        # Uncached test
        start_time = time.perf_counter()
        uncached_results = await asyncio.gather(
            *[fetch_share(use_cache=False) for _ in range(500)],
            return_exceptions=True
        )
        uncached_duration = time.perf_counter() - start_time

        uncached_successes = [r for r in uncached_results if isinstance(r, dict) and r["success"]]
        uncached_failures = [r for r in uncached_results if not isinstance(r, dict) or not r.get("success")]
        uncached_durations = [r["duration_ms"] for r in uncached_successes]

        result_uncached = LoadTestResult(
            test_name="Public Share Pages (uncached, 500 concurrent)",
            total_requests=len(uncached_results),
            successful_requests=len(uncached_successes),
            failed_requests=len(uncached_failures),
            duration_seconds=uncached_duration,
            requests_per_second=len(uncached_results) / uncached_duration if uncached_duration > 0 else 0,
            p50_ms=statistics.median(uncached_durations) if uncached_durations else 0,
            p95_ms=self._percentile(uncached_durations, 95) if uncached_durations else 0,
            p99_ms=self._percentile(uncached_durations, 99) if uncached_durations else 0,
            min_ms=min(uncached_durations) if uncached_durations else 0,
            max_ms=max(uncached_durations) if uncached_durations else 0,
            avg_ms=statistics.mean(uncached_durations) if uncached_durations else 0,
            errors=[str(f) for f in uncached_failures],
        )
        self.results.append(result_uncached)
        self._print_test_result(result_uncached, target_p95=1000)

        # Step 3: Test cached requests
        print(f"  {Fore.CYAN}Testing cached requests (500 concurrent)...{Style.RESET_ALL}")

        start_time = time.perf_counter()
        cached_results = await asyncio.gather(
            *[fetch_share(use_cache=True) for _ in range(500)],
            return_exceptions=True
        )
        cached_duration = time.perf_counter() - start_time

        cached_successes = [r for r in cached_results if isinstance(r, dict) and r["success"]]
        cached_failures = [r for r in cached_results if not isinstance(r, dict) or not r.get("success")]
        cached_durations = [r["duration_ms"] for r in cached_successes]

        result_cached = LoadTestResult(
            test_name="Public Share Pages (cached, 500 concurrent)",
            total_requests=len(cached_results),
            successful_requests=len(cached_successes),
            failed_requests=len(cached_failures),
            duration_seconds=cached_duration,
            requests_per_second=len(cached_results) / cached_duration if cached_duration > 0 else 0,
            p50_ms=statistics.median(cached_durations) if cached_durations else 0,
            p95_ms=self._percentile(cached_durations, 95) if cached_durations else 0,
            p99_ms=self._percentile(cached_durations, 99) if cached_durations else 0,
            min_ms=min(cached_durations) if cached_durations else 0,
            max_ms=max(cached_durations) if cached_durations else 0,
            avg_ms=statistics.mean(cached_durations) if cached_durations else 0,
            errors=[str(f) for f in cached_failures],
        )
        self.results.append(result_cached)
        self._print_test_result(result_cached, target_p95=50)

    # ==================== Share Creation Load Test ====================

    async def test_share_creation(self) -> None:
        """Test share creation under load.

        Target: p95 < 500ms with 50 concurrent users
        """
        print(f"\n{Fore.YELLOW}[TEST SUITE] Share Creation Load Test{Style.RESET_ALL}")

        print(f"  {Fore.CYAN}Testing share creation (50 concurrent users)...{Style.RESET_ALL}")

        async def create_share(index: int):
            """Create share with timing."""
            async with httpx.AsyncClient(base_url=self.api_url, timeout=30.0) as client:
                start = time.perf_counter()
                response = await client.post(
                    "/v1/user-shares",
                    json={
                        "recipient_id": 2,
                        "listing_id": (index % 10) + 1,  # Cycle through 10 listings
                        "message": f"Load test share {index}",
                    }
                )
                duration = (time.perf_counter() - start) * 1000
                return {
                    "success": response.status_code == 201,
                    "duration_ms": duration,
                    "status": response.status_code,
                }

        # Run concurrent requests
        start_time = time.perf_counter()
        results = await asyncio.gather(*[create_share(i) for i in range(50)], return_exceptions=True)
        total_duration = time.perf_counter() - start_time

        # Process results
        successes = [r for r in results if isinstance(r, dict) and r["success"]]
        failures = [r for r in results if not isinstance(r, dict) or not r.get("success")]
        durations = [r["duration_ms"] for r in successes]

        result = LoadTestResult(
            test_name="Share Creation (50 concurrent users)",
            total_requests=len(results),
            successful_requests=len(successes),
            failed_requests=len(failures),
            duration_seconds=total_duration,
            requests_per_second=len(results) / total_duration if total_duration > 0 else 0,
            p50_ms=statistics.median(durations) if durations else 0,
            p95_ms=self._percentile(durations, 95) if durations else 0,
            p99_ms=self._percentile(durations, 99) if durations else 0,
            min_ms=min(durations) if durations else 0,
            max_ms=max(durations) if durations else 0,
            avg_ms=statistics.mean(durations) if durations else 0,
            errors=[str(f) for f in failures],
        )
        self.results.append(result)
        self._print_test_result(result, target_p95=500)

    # ==================== Database Connection Pool Test ====================

    async def test_database_connections(self) -> None:
        """Test database connection pool under load.

        Monitors:
        - No connection leaks
        - Max connections not exceeded
        - Connection reuse
        """
        print(f"\n{Fore.YELLOW}[TEST SUITE] Database Connection Pool Test{Style.RESET_ALL}")

        print(f"  {Fore.CYAN}Testing connection pool (200 concurrent queries)...{Style.RESET_ALL}")

        async def query_database(index: int):
            """Execute query with timing."""
            async with httpx.AsyncClient(base_url=self.api_url, timeout=30.0) as client:
                start = time.perf_counter()
                # Mix of read and write operations
                if index % 2 == 0:
                    # Read operation
                    response = await client.get("/v1/collections")
                else:
                    # Write operation
                    response = await client.post(
                        "/v1/collections",
                        json={
                            "name": f"Connection test {index}",
                            "description": "Testing connection pool",
                            "visibility": "private",
                        }
                    )
                duration = (time.perf_counter() - start) * 1000
                return {
                    "success": response.status_code in [200, 201],
                    "duration_ms": duration,
                    "status": response.status_code,
                }

        # Run concurrent requests
        start_time = time.perf_counter()
        results = await asyncio.gather(*[query_database(i) for i in range(200)], return_exceptions=True)
        total_duration = time.perf_counter() - start_time

        # Process results
        successes = [r for r in results if isinstance(r, dict) and r["success"]]
        failures = [r for r in results if not isinstance(r, dict) or not r.get("success")]
        durations = [r["duration_ms"] for r in successes]

        result = LoadTestResult(
            test_name="Database Connection Pool (200 concurrent queries)",
            total_requests=len(results),
            successful_requests=len(successes),
            failed_requests=len(failures),
            duration_seconds=total_duration,
            requests_per_second=len(results) / total_duration if total_duration > 0 else 0,
            p50_ms=statistics.median(durations) if durations else 0,
            p95_ms=self._percentile(durations, 95) if durations else 0,
            p99_ms=self._percentile(durations, 99) if durations else 0,
            min_ms=min(durations) if durations else 0,
            max_ms=max(durations) if durations else 0,
            avg_ms=statistics.mean(durations) if durations else 0,
            errors=[str(f) for f in failures],
        )
        self.results.append(result)

        # Check for connection exhaustion
        connection_errors = [e for e in result.errors if "connection" in str(e).lower()]
        if connection_errors:
            print(f"  {Fore.RED}✗ Connection pool exhaustion detected{Style.RESET_ALL}")
            print(f"    {Fore.RED}└─ {len(connection_errors)} connection errors{Style.RESET_ALL}")
        else:
            print(f"  {Fore.GREEN}✓ No connection pool exhaustion{Style.RESET_ALL}")

        self._print_test_result(result, target_p95=300)

    # ==================== Helper Methods ====================

    async def _create_test_collection_with_items(self, num_items: int) -> int | None:
        """Create collection with specified number of items.

        Args:
            num_items: Number of items to add

        Returns:
            Collection ID or None if failed
        """
        async with httpx.AsyncClient(base_url=self.api_url, timeout=30.0) as client:
            # Create collection
            response = await client.post(
                "/v1/collections",
                json={
                    "name": "Load Test Collection",
                    "description": f"Collection with {num_items} items for load testing",
                    "visibility": "private",
                }
            )

            if response.status_code != 201:
                return None

            collection_id = response.json()["id"]

            # Add items (assume listings 1-100 exist)
            for i in range(num_items):
                await client.post(
                    f"/v1/collections/{collection_id}/items",
                    json={
                        "listing_id": (i % 100) + 1,  # Cycle through 100 listings
                        "status": "undecided",
                        "notes": f"Load test item {i}",
                    }
                )

            return collection_id

    async def _create_test_share(self) -> tuple[str | None, int | None]:
        """Create test share.

        Returns:
            Tuple of (share_token, listing_id) or (None, None) if failed
        """
        async with httpx.AsyncClient(base_url=self.api_url, timeout=30.0) as client:
            response = await client.post(
                "/v1/user-shares",
                json={
                    "recipient_id": 2,
                    "listing_id": 1,
                    "message": "Load test share",
                }
            )

            if response.status_code != 201:
                return None, None

            data = response.json()
            return data["share_token"], data["listing_id"]

    def _percentile(self, data: list[float], percentile: int) -> float:
        """Calculate percentile.

        Args:
            data: List of values
            percentile: Percentile (0-100)

        Returns:
            Percentile value
        """
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def _print_test_result(self, result: LoadTestResult, target_p95: float) -> None:
        """Print test result.

        Args:
            result: Test result
            target_p95: Target p95 in ms
        """
        p95_pass = result.p95_ms <= target_p95
        p95_status = f"{Fore.GREEN}✓ PASS" if p95_pass else f"{Fore.RED}✗ FAIL"

        print(f"\n  {Fore.CYAN}Results:{Style.RESET_ALL}")
        print(f"    Total Requests: {result.total_requests}")
        print(f"    Successful: {Fore.GREEN}{result.successful_requests}{Style.RESET_ALL}")
        print(f"    Failed: {Fore.RED}{result.failed_requests}{Style.RESET_ALL}")
        print(f"    Duration: {result.duration_seconds:.2f}s")
        print(f"    Throughput: {result.requests_per_second:.2f} req/s")
        print(f"\n  {Fore.CYAN}Response Times:{Style.RESET_ALL}")
        print(f"    p50: {result.p50_ms:.2f}ms")
        print(f"    p95: {result.p95_ms:.2f}ms {p95_status} (target: {target_p95}ms){Style.RESET_ALL}")
        print(f"    p99: {result.p99_ms:.2f}ms")
        print(f"    min: {result.min_ms:.2f}ms")
        print(f"    max: {result.max_ms:.2f}ms")
        print(f"    avg: {result.avg_ms:.2f}ms")

        if result.failed_requests > 0:
            print(f"\n  {Fore.RED}Errors ({len(result.errors)}):{Style.RESET_ALL}")
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"    {Fore.RED}- {error}{Style.RESET_ALL}")

    def _generate_summary(self) -> dict[str, Any]:
        """Generate test summary.

        Returns:
            Summary dictionary
        """
        total_requests = sum(r.total_requests for r in self.results)
        total_failures = sum(r.failed_requests for r in self.results)

        return {
            "total_tests": len(self.results),
            "total_requests": total_requests,
            "total_failures": total_failures,
            "tests": [
                {
                    "name": r.test_name,
                    "requests": r.total_requests,
                    "failures": r.failed_requests,
                    "p95_ms": r.p95_ms,
                    "throughput_rps": r.requests_per_second,
                }
                for r in self.results
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _print_results(self) -> None:
        """Print overall results summary."""
        summary = self._generate_summary()

        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.CYAN}LOAD TESTING SUMMARY")
        print(f"{Fore.CYAN}{'=' * 80}\n")

        print(f"Total Tests: {summary['total_tests']}")
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Total Failures: {Fore.RED}{summary['total_failures']}{Style.RESET_ALL}\n")

        print(f"{Fore.YELLOW}Test Results:{Style.RESET_ALL}")
        for test in summary["tests"]:
            print(f"  {test['name']}")
            print(f"    Requests: {test['requests']}, Failures: {test['failures']}")
            print(f"    p95: {test['p95_ms']:.2f}ms, Throughput: {test['throughput_rps']:.2f} req/s")

        print(f"\n{Fore.CYAN}{'=' * 80}\n")

    async def _save_report(self, summary: dict[str, Any]) -> None:
        """Save detailed report to file.

        Args:
            summary: Test summary
        """
        TEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        report_path = TEST_RESULTS_DIR / "performance-load-test-report.md"

        # Generate markdown report
        report = [
            "# Performance Load Test Report - Collections Sharing",
            "",
            f"**Generated:** {datetime.utcnow().isoformat()}",
            "",
            "## Summary",
            "",
            f"- **Total Tests:** {summary['total_tests']}",
            f"- **Total Requests:** {summary['total_requests']}",
            f"- **Total Failures:** {summary['total_failures']}",
            "",
            "## Test Results",
            "",
        ]

        for result in self.results:
            report.append(f"### {result.test_name}")
            report.append("")
            report.append("**Metrics:**")
            report.append("")
            report.append(f"- Total Requests: {result.total_requests}")
            report.append(f"- Successful: {result.successful_requests}")
            report.append(f"- Failed: {result.failed_requests}")
            report.append(f"- Duration: {result.duration_seconds:.2f}s")
            report.append(f"- Throughput: {result.requests_per_second:.2f} req/s")
            report.append("")
            report.append("**Response Times:**")
            report.append("")
            report.append(f"- p50: {result.p50_ms:.2f}ms")
            report.append(f"- p95: {result.p95_ms:.2f}ms")
            report.append(f"- p99: {result.p99_ms:.2f}ms")
            report.append(f"- min: {result.min_ms:.2f}ms")
            report.append(f"- max: {result.max_ms:.2f}ms")
            report.append(f"- avg: {result.avg_ms:.2f}ms")
            report.append("")

            if result.errors:
                report.append("**Errors:**")
                report.append("")
                for error in result.errors[:10]:  # Show first 10
                    report.append(f"- {error}")
                report.append("")

        # Performance targets comparison
        report.append("## Performance Targets")
        report.append("")
        report.append("| Test | Target p95 | Actual p95 | Status |")
        report.append("|------|-----------|-----------|---------|")

        targets = {
            "Collections Endpoint": 200,
            "Public Share Pages (uncached": 1000,
            "Public Share Pages (cached": 50,
            "Share Creation": 500,
            "Database Connection Pool": 300,
        }

        for result in self.results:
            for key, target in targets.items():
                if key in result.test_name:
                    status = "✓ PASS" if result.p95_ms <= target else "✗ FAIL"
                    report.append(
                        f"| {result.test_name} | {target}ms | {result.p95_ms:.2f}ms | {status} |"
                    )
                    break

        report.append("")

        # Write report
        report_path.write_text("\n".join(report))
        print(f"{Fore.GREEN}Report saved to: {report_path}{Style.RESET_ALL}\n")


async def main() -> None:
    """Main entry point."""
    load_test = LoadTest()

    try:
        summary = await load_test.run_all_tests()

        # Exit with error code if any failures
        if summary["total_failures"] > 0:
            print(f"{Fore.RED}LOAD TEST FAILURES DETECTED{Style.RESET_ALL}")
            sys.exit(1)
        else:
            print(f"{Fore.GREEN}Load testing completed successfully{Style.RESET_ALL}")
            sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}Load testing failed: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
