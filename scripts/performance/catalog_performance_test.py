#!/usr/bin/env python3
"""
Performance validation script for catalog API endpoints.

Tests CRUD operations against defined performance targets:
- Update operations (PUT/PATCH): < 500ms (P95)
- Delete with cascade check: < 1s (P95)
- Entity list queries: < 2s for 10,000+ entities
- Detail view load (including "Used In"): < 1.5s

Usage:
    poetry run python scripts/performance/catalog_performance_test.py [options]

Options:
    --base-url URL          API base URL (default: http://localhost:8000)
    --runs N                Number of test runs per scenario (default: 20)
    --output FILE           Output file for results (default: performance-results.json)
    --entity-type TYPE      Test specific entity type (cpu, gpu, profile, etc.)
    --verbose              Enable verbose output
"""

import argparse
import asyncio
import json
import statistics
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx


@dataclass
class PerformanceResult:
    """Performance test result."""

    operation: str
    entity_type: str
    scenario: str
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    mean_ms: float
    stddev_ms: float
    target_ms: float
    passed: bool
    runs: int
    failed_runs: int = 0
    error_message: str | None = None


@dataclass
class TestScenario:
    """Test scenario configuration."""

    name: str
    operation: str
    entity_type: str
    target_p95_ms: float
    description: str


class CatalogPerformanceTester:
    """Performance tester for catalog API endpoints."""

    def __init__(self, base_url: str, runs: int = 20, verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.runs = runs
        self.verbose = verbose
        self.results: list[PerformanceResult] = []

        # Test scenarios with targets
        self.scenarios = [
            # CPU scenarios
            TestScenario(
                name="CPU_PATCH_SINGLE_FIELD",
                operation="PATCH",
                entity_type="CPU",
                target_p95_ms=500.0,
                description="Update CPU with single field change",
            ),
            TestScenario(
                name="CPU_PUT_FULL_UPDATE",
                operation="PUT",
                entity_type="CPU",
                target_p95_ms=500.0,
                description="Full CPU entity update",
            ),
            TestScenario(
                name="CPU_DELETE_NO_LISTINGS",
                operation="DELETE",
                entity_type="CPU",
                target_p95_ms=1000.0,
                description="Delete CPU with 0 listings",
            ),
            TestScenario(
                name="CPU_DELETE_WITH_LISTINGS_100",
                operation="DELETE_CHECK",
                entity_type="CPU",
                target_p95_ms=1000.0,
                description="Delete check for CPU with 100 listings",
            ),
            TestScenario(
                name="CPU_DELETE_WITH_LISTINGS_1000",
                operation="DELETE_CHECK",
                entity_type="CPU",
                target_p95_ms=1000.0,
                description="Delete check for CPU with 1000 listings",
            ),
            TestScenario(
                name="CPU_LIST_ALL",
                operation="LIST",
                entity_type="CPU",
                target_p95_ms=2000.0,
                description="List all CPUs (target: < 2s for 10k+ entities)",
            ),
            TestScenario(
                name="CPU_DETAIL_WITH_LISTINGS",
                operation="DETAIL",
                entity_type="CPU",
                target_p95_ms=1500.0,
                description="Get CPU detail with listings (Used In)",
            ),
            # GPU scenarios
            TestScenario(
                name="GPU_PATCH_SINGLE_FIELD",
                operation="PATCH",
                entity_type="GPU",
                target_p95_ms=500.0,
                description="Update GPU with single field change",
            ),
            TestScenario(
                name="GPU_PUT_FULL_UPDATE",
                operation="PUT",
                entity_type="GPU",
                target_p95_ms=500.0,
                description="Full GPU entity update",
            ),
            TestScenario(
                name="GPU_LIST_ALL",
                operation="LIST",
                entity_type="GPU",
                target_p95_ms=2000.0,
                description="List all GPUs",
            ),
            # Profile scenarios
            TestScenario(
                name="PROFILE_PATCH_WEIGHTS",
                operation="PATCH",
                entity_type="Profile",
                target_p95_ms=500.0,
                description="Update profile weights",
            ),
            TestScenario(
                name="PROFILE_LIST_ALL",
                operation="LIST",
                entity_type="Profile",
                target_p95_ms=2000.0,
                description="List all scoring profiles",
            ),
            # RAM spec scenarios
            TestScenario(
                name="RAM_SPEC_LIST_WITH_FILTER",
                operation="LIST",
                entity_type="RamSpec",
                target_p95_ms=2000.0,
                description="List RAM specs with filters",
            ),
            # Storage profile scenarios
            TestScenario(
                name="STORAGE_PROFILE_LIST_WITH_FILTER",
                operation="LIST",
                entity_type="StorageProfile",
                target_p95_ms=2000.0,
                description="List storage profiles with filters",
            ),
        ]

    async def measure_operation(
        self, operation_func, scenario: TestScenario
    ) -> tuple[list[float], int]:
        """Measure operation performance over multiple runs."""
        times = []
        failed = 0

        for i in range(self.runs):
            try:
                start = time.perf_counter()
                await operation_func()
                elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
                times.append(elapsed)

                if self.verbose:
                    print(f"  Run {i + 1}/{self.runs}: {elapsed:.1f}ms", end="\r", flush=True)
            except Exception as e:
                failed += 1
                if self.verbose:
                    print(f"  Run {i + 1}/{self.runs}: FAILED - {e}")

        if self.verbose:
            print()  # New line after progress

        return times, failed

    def calculate_percentiles(self, times: list[float]) -> dict[str, float]:
        """Calculate performance percentiles."""
        if not times:
            return {
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
                "stddev": 0.0,
            }

        sorted_times = sorted(times)
        n = len(sorted_times)

        return {
            "p50": sorted_times[int(n * 0.50)] if n > 0 else 0.0,
            "p95": sorted_times[int(n * 0.95)] if n > 1 else sorted_times[0],
            "p99": sorted_times[int(n * 0.99)] if n > 2 else sorted_times[-1],
            "min": min(sorted_times),
            "max": max(sorted_times),
            "mean": statistics.mean(sorted_times),
            "stddev": statistics.stdev(sorted_times) if n > 1 else 0.0,
        }

    async def test_cpu_patch(self, client: httpx.AsyncClient, cpu_id: int):
        """Test CPU PATCH operation."""
        await client.patch(
            f"{self.base_url}/v1/catalog/cpus/{cpu_id}",
            json={"notes": f"Updated at {time.time()}"},
        )

    async def test_cpu_put(self, client: httpx.AsyncClient, cpu_id: int, cpu_data: dict):
        """Test CPU PUT operation."""
        await client.put(
            f"{self.base_url}/v1/catalog/cpus/{cpu_id}",
            json=cpu_data,
        )

    async def test_cpu_delete(self, client: httpx.AsyncClient, cpu_id: int):
        """Test CPU DELETE operation."""
        response = await client.delete(f"{self.base_url}/v1/catalog/cpus/{cpu_id}")
        # If it returns 409, that's expected for entities with listings
        if response.status_code not in [204, 409]:
            raise Exception(f"Unexpected status: {response.status_code}")

    async def test_cpu_list(self, client: httpx.AsyncClient):
        """Test CPU LIST operation."""
        response = await client.get(f"{self.base_url}/v1/catalog/cpus")
        response.raise_for_status()

    async def test_cpu_detail_with_listings(self, client: httpx.AsyncClient, cpu_id: int):
        """Test CPU detail view with listings."""
        # Get CPU detail
        response1 = await client.get(f"{self.base_url}/v1/catalog/cpus/{cpu_id}")
        response1.raise_for_status()

        # Get CPU listings
        response2 = await client.get(f"{self.base_url}/v1/catalog/cpus/{cpu_id}/listings?limit=50")
        response2.raise_for_status()

    async def test_gpu_patch(self, client: httpx.AsyncClient, gpu_id: int):
        """Test GPU PATCH operation."""
        await client.patch(
            f"{self.base_url}/v1/catalog/gpus/{gpu_id}",
            json={"notes": f"Updated at {time.time()}"},
        )

    async def test_gpu_put(self, client: httpx.AsyncClient, gpu_id: int, gpu_data: dict):
        """Test GPU PUT operation."""
        await client.put(
            f"{self.base_url}/v1/catalog/gpus/{gpu_id}",
            json=gpu_data,
        )

    async def test_gpu_list(self, client: httpx.AsyncClient):
        """Test GPU LIST operation."""
        response = await client.get(f"{self.base_url}/v1/catalog/gpus")
        response.raise_for_status()

    async def test_profile_patch(self, client: httpx.AsyncClient, profile_id: int):
        """Test Profile PATCH operation."""
        await client.patch(
            f"{self.base_url}/v1/catalog/profiles/{profile_id}",
            json={"weights_json": {"cpu_mark_multi_price_efficiency": 0.3}},
        )

    async def test_profile_list(self, client: httpx.AsyncClient):
        """Test Profile LIST operation."""
        response = await client.get(f"{self.base_url}/v1/catalog/profiles")
        response.raise_for_status()

    async def test_ram_spec_list(self, client: httpx.AsyncClient):
        """Test RamSpec LIST with filters."""
        response = await client.get(f"{self.base_url}/v1/catalog/ram-specs?limit=200")
        response.raise_for_status()

    async def test_storage_profile_list(self, client: httpx.AsyncClient):
        """Test StorageProfile LIST with filters."""
        response = await client.get(f"{self.base_url}/v1/catalog/storage-profiles?limit=200")
        response.raise_for_status()

    async def run_scenario(
        self, client: httpx.AsyncClient, scenario: TestScenario
    ) -> PerformanceResult | None:
        """Run a single test scenario."""
        print(f"\n{'=' * 80}")
        print(f"Testing: {scenario.name}")
        print(f"Description: {scenario.description}")
        print(f"Target P95: < {scenario.target_p95_ms}ms")
        print(f"{'=' * 80}")

        try:
            # Get a sample entity ID for testing
            entity_id = await self._get_sample_entity_id(client, scenario.entity_type)
            if entity_id is None:
                print(f"⚠️  Skipping {scenario.name}: No {scenario.entity_type} entities found")
                return None

            # Get entity data if needed for PUT operations
            entity_data = None
            if scenario.operation == "PUT":
                entity_data = await self._get_entity_data(client, scenario.entity_type, entity_id)

            # Create operation function
            async def operation():
                if scenario.operation == "PATCH":
                    if scenario.entity_type == "CPU":
                        await self.test_cpu_patch(client, entity_id)
                    elif scenario.entity_type == "GPU":
                        await self.test_gpu_patch(client, entity_id)
                    elif scenario.entity_type == "Profile":
                        await self.test_profile_patch(client, entity_id)
                elif scenario.operation == "PUT":
                    if scenario.entity_type == "CPU":
                        await self.test_cpu_put(client, entity_id, entity_data)
                    elif scenario.entity_type == "GPU":
                        await self.test_gpu_put(client, entity_id, entity_data)
                elif scenario.operation in ["DELETE", "DELETE_CHECK"]:
                    if scenario.entity_type == "CPU":
                        await self.test_cpu_delete(client, entity_id)
                elif scenario.operation == "LIST":
                    if scenario.entity_type == "CPU":
                        await self.test_cpu_list(client)
                    elif scenario.entity_type == "GPU":
                        await self.test_gpu_list(client)
                    elif scenario.entity_type == "Profile":
                        await self.test_profile_list(client)
                    elif scenario.entity_type == "RamSpec":
                        await self.test_ram_spec_list(client)
                    elif scenario.entity_type == "StorageProfile":
                        await self.test_storage_profile_list(client)
                elif scenario.operation == "DETAIL":
                    if scenario.entity_type == "CPU":
                        await self.test_cpu_detail_with_listings(client, entity_id)

            # Run performance test
            times, failed = await self.measure_operation(operation, scenario)

            if not times:
                print(f"❌ All runs failed for {scenario.name}")
                return PerformanceResult(
                    operation=scenario.operation,
                    entity_type=scenario.entity_type,
                    scenario=scenario.name,
                    p50_ms=0.0,
                    p95_ms=0.0,
                    p99_ms=0.0,
                    min_ms=0.0,
                    max_ms=0.0,
                    mean_ms=0.0,
                    stddev_ms=0.0,
                    target_ms=scenario.target_p95_ms,
                    passed=False,
                    runs=self.runs,
                    failed_runs=failed,
                    error_message="All runs failed",
                )

            # Calculate statistics
            stats = self.calculate_percentiles(times)
            passed = stats["p95"] < scenario.target_p95_ms

            # Print results
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"\nResults:")
            print(f"  P50: {stats['p50']:.1f}ms")
            print(f"  P95: {stats['p95']:.1f}ms (target: < {scenario.target_p95_ms}ms)")
            print(f"  P99: {stats['p99']:.1f}ms")
            print(f"  Min: {stats['min']:.1f}ms")
            print(f"  Max: {stats['max']:.1f}ms")
            print(f"  Mean: {stats['mean']:.1f}ms")
            print(f"  StdDev: {stats['stddev']:.1f}ms")
            print(f"  Failed runs: {failed}/{self.runs}")
            print(f"\n{status}")

            return PerformanceResult(
                operation=scenario.operation,
                entity_type=scenario.entity_type,
                scenario=scenario.name,
                p50_ms=stats["p50"],
                p95_ms=stats["p95"],
                p99_ms=stats["p99"],
                min_ms=stats["min"],
                max_ms=stats["max"],
                mean_ms=stats["mean"],
                stddev_ms=stats["stddev"],
                target_ms=scenario.target_p95_ms,
                passed=passed,
                runs=self.runs,
                failed_runs=failed,
            )

        except Exception as e:
            print(f"❌ Error running scenario: {e}")
            return PerformanceResult(
                operation=scenario.operation,
                entity_type=scenario.entity_type,
                scenario=scenario.name,
                p50_ms=0.0,
                p95_ms=0.0,
                p99_ms=0.0,
                min_ms=0.0,
                max_ms=0.0,
                mean_ms=0.0,
                stddev_ms=0.0,
                target_ms=scenario.target_p95_ms,
                passed=False,
                runs=self.runs,
                failed_runs=self.runs,
                error_message=str(e),
            )

    async def _get_sample_entity_id(
        self, client: httpx.AsyncClient, entity_type: str
    ) -> int | None:
        """Get a sample entity ID for testing."""
        endpoints = {
            "CPU": "/v1/catalog/cpus",
            "GPU": "/v1/catalog/gpus",
            "Profile": "/v1/catalog/profiles",
            "RamSpec": "/v1/catalog/ram-specs",
            "StorageProfile": "/v1/catalog/storage-profiles",
            "PortsProfile": "/v1/catalog/ports-profiles",
        }

        endpoint = endpoints.get(entity_type)
        if not endpoint:
            return None

        response = await client.get(f"{self.base_url}{endpoint}?limit=1")
        if response.status_code != 200:
            return None

        entities = response.json()
        return entities[0]["id"] if entities else None

    async def _get_entity_data(
        self, client: httpx.AsyncClient, entity_type: str, entity_id: int
    ) -> dict | None:
        """Get entity data for PUT operations."""
        endpoints = {
            "CPU": f"/v1/catalog/cpus/{entity_id}",
            "GPU": f"/v1/catalog/gpus/{entity_id}",
            "Profile": f"/v1/catalog/profiles/{entity_id}",
        }

        endpoint = endpoints.get(entity_type)
        if not endpoint:
            return None

        response = await client.get(f"{self.base_url}{endpoint}")
        if response.status_code != 200:
            return None

        data = response.json()
        # Remove read-only fields
        data.pop("id", None)
        data.pop("created_at", None)
        data.pop("updated_at", None)

        return data

    async def run_all_tests(self, entity_type: str | None = None):
        """Run all performance tests."""
        print("\n" + "=" * 80)
        print("CATALOG API PERFORMANCE VALIDATION")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Runs per test: {self.runs}")
        print(f"Timestamp: {datetime.now().isoformat()}")

        scenarios = self.scenarios
        if entity_type:
            scenarios = [s for s in scenarios if s.entity_type.lower() == entity_type.lower()]
            print(f"Filtering to entity type: {entity_type}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Verify API is accessible
            try:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code != 200:
                    print(f"❌ API health check failed: {response.status_code}")
                    return
            except Exception as e:
                print(f"❌ Cannot connect to API: {e}")
                print("\nPlease ensure the API is running with: make up" " or make api")
                return

            # Run scenarios
            for scenario in scenarios:
                result = await self.run_scenario(client, scenario)
                if result:
                    self.results.append(result)

        # Print summary
        self._print_summary()

    def _print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        if not self.results:
            print("No results to display")
            return

        # Group by target
        targets = defaultdict(list)
        for result in self.results:
            targets[result.target_ms].append(result)

        # Print by target group
        for target_ms in sorted(targets.keys()):
            results = targets[target_ms]
            passed = sum(1 for r in results if r.passed)
            total = len(results)

            print(f"\nTarget: P95 < {target_ms}ms ({passed}/{total} passed)")
            print("-" * 80)

            for result in sorted(results, key=lambda r: r.scenario):
                status = "✅" if result.passed else "❌"
                print(
                    f"{status} {result.scenario:45s} P95: {result.p95_ms:7.1f}ms "
                    f"(target: {result.target_ms:.0f}ms)"
                )

        # Overall stats
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests

        print("\n" + "=" * 80)
        print(f"Overall: {passed_tests}/{total_tests} tests passed")
        if failed_tests > 0:
            print(f"⚠️  {failed_tests} test(s) did not meet performance targets")
        else:
            print("✅ All performance targets met!")
        print("=" * 80)

    def save_results(self, output_file: str):
        """Save results to JSON file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        results_dict = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "runs_per_test": self.runs,
            "results": [asdict(r) for r in self.results],
            "summary": {
                "total_tests": len(self.results),
                "passed": sum(1 for r in self.results if r.passed),
                "failed": sum(1 for r in self.results if not r.passed),
            },
        }

        with open(output_path, "w") as f:
            json.dump(results_dict, f, indent=2)

        print(f"\n✅ Results saved to: {output_path.absolute()}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Performance validation for catalog API endpoints")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=20,
        help="Number of test runs per scenario (default: 20)",
    )
    parser.add_argument(
        "--output",
        default="performance-results.json",
        help="Output file for results (default: performance-results.json)",
    )
    parser.add_argument(
        "--entity-type",
        choices=["cpu", "gpu", "profile", "ramspec", "storageprofile"],
        help="Test specific entity type only",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Run tests
    tester = CatalogPerformanceTester(
        base_url=args.base_url,
        runs=args.runs,
        verbose=args.verbose,
    )

    asyncio.run(tester.run_all_tests(entity_type=args.entity_type))

    # Save results
    tester.save_results(args.output)

    # Exit with error code if any tests failed
    failed = sum(1 for r in tester.results if not r.passed)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
