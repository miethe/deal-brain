"""Integration tests for Amazon import enhancement (Phase 4).

These tests cover:
- Amazon product scraping
- NLP-based component extraction
- Fuzzy catalog matching
- End-to-end import workflow
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dealbrain_api.importers.amazon_scraper import (
    AmazonScraperError,
    scrape_amazon_product,
)
from dealbrain_api.importers.nlp_extractor import (
    ExtractionResult,
    NLPExtractor,
    extract_from_amazon_data,
)
from dealbrain_api.models.catalog import Cpu, Gpu
from dealbrain_api.services.catalog_matcher import (
    CatalogMatcher,
    match_extracted_components,
    normalize_component_name,
)


# Sample HTML for testing (simplified Amazon product page)
SAMPLE_AMAZON_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Product</title></head>
<body>
    <span id="productTitle">Beelink Mini PC, Intel Core i7-12700H 12th Gen 14 Cores,
    16GB DDR4 RAM, 512GB NVMe SSD, Intel Iris Xe Graphics</span>

    <div id="feature-bullets">
        <ul>
            <li>12th Gen Intel Core i7-12700H Processor (up to 4.7GHz)</li>
            <li>16GB DDR4 3200MHz RAM</li>
            <li>512GB NVMe PCIe SSD</li>
            <li>Intel Iris Xe Graphics</li>
            <li>Windows 11 Pro</li>
        </ul>
    </div>

    <table id="productDetails_techSpec_section_1">
        <tr>
            <th>Manufacturer</th>
            <td>Beelink</td>
        </tr>
        <tr>
            <th>Model Number</th>
            <td>SEi12-i7-12700H</td>
        </tr>
    </table>

    <span class="a-price-whole">$489.99</span>
</body>
</html>
"""


class TestAmazonScraper:
    """Test suite for Amazon product scraping."""

    @pytest.mark.asyncio
    async def test_scrape_amazon_product_success(self):
        """Test successful Amazon product scraping."""
        with patch("dealbrain_api.importers.amazon_scraper.httpx.AsyncClient") as mock_client:
            # Mock HTTP response
            mock_response = MagicMock()
            mock_response.content = SAMPLE_AMAZON_HTML.encode("utf-8")
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Scrape product
            result = await scrape_amazon_product("https://www.amazon.com/dp/TEST123")

            # Assertions
            assert result["title"] != ""
            assert "Intel Core i7-12700H" in result["title"]
            assert result["manufacturer"] == "Beelink"
            assert result["model"] == "SEi12-i7-12700H"
            assert len(result["bullet_points"]) > 0
            assert result["specs"]["Manufacturer"] == "Beelink"

    @pytest.mark.asyncio
    async def test_scrape_amazon_product_http_error(self):
        """Test Amazon scraping with HTTP error."""
        import httpx

        with patch("dealbrain_api.importers.amazon_scraper.httpx.AsyncClient") as mock_client:
            # Mock HTTP error using httpx.RequestError
            error = httpx.RequestError("Connection failed")

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=error
            )

            # Should raise AmazonScraperError
            with pytest.raises(AmazonScraperError):
                await scrape_amazon_product("https://www.amazon.com/dp/INVALID")

    @pytest.mark.asyncio
    async def test_scrape_amazon_product_missing_elements(self):
        """Test scraping handles missing elements gracefully."""
        minimal_html = "<html><body><span id='productTitle'>Test Product</span></body></html>"

        with patch("dealbrain_api.importers.amazon_scraper.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.content = minimal_html.encode("utf-8")
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await scrape_amazon_product("https://www.amazon.com/dp/TEST123")

            # Should return empty strings/dicts for missing data
            assert result["title"] == "Test Product"
            assert result["manufacturer"] == ""
            assert result["model"] == ""
            assert result["specs"] == {}


class TestNLPExtractor:
    """Test suite for NLP component extraction."""

    def test_extract_cpu_intel_core(self):
        """Test CPU extraction for Intel Core processors."""
        extractor = NLPExtractor()

        test_cases = [
            ("Intel Core i7-12700K Mini PC", "i7", "12700"),
            ("Beelink with i5-13600 processor", "i5", "13600"),
            ("Core i9-13900KS Desktop", "i9", "13900"),
        ]

        for text, expected_series, expected_model in test_cases:
            result = extractor.extract_cpu(text)
            assert result is not None
            assert expected_series in result.value.lower()
            assert expected_model in result.value
            assert result.confidence == "high"

    def test_extract_cpu_amd_ryzen(self):
        """Test CPU extraction for AMD Ryzen processors."""
        extractor = NLPExtractor()

        test_cases = [
            ("AMD Ryzen 5 5600X Mini PC", "5", "5600"),
            ("Ryzen 7 7700X Desktop", "7", "7700"),
            ("Mini PC with Ryzen 9 7950X3D", "9", "7950"),
        ]

        for text, expected_series, expected_model in test_cases:
            result = extractor.extract_cpu(text)
            assert result is not None
            assert expected_series in result.value
            assert expected_model in result.value
            assert result.confidence == "high"

    def test_extract_ram_with_generation(self):
        """Test RAM extraction with DDR generation."""
        extractor = NLPExtractor()

        test_cases = [
            ("16GB DDR4 RAM", 16, "DDR4"),
            ("32GB DDR5 Memory", 32, "DDR5"),
            ("8GB DDR3", 8, "DDR3"),
        ]

        for text, expected_capacity, expected_type in test_cases:
            result = extractor.extract_ram(text)
            assert result is not None
            assert result["capacity_gb"] == expected_capacity
            assert result["type"] == expected_type
            assert result["confidence"] == "high"

    def test_extract_storage_nvme(self):
        """Test storage extraction for NVMe SSDs."""
        extractor = NLPExtractor()

        test_cases = [
            ("512GB NVMe SSD", 512, "NVMe SSD"),
            ("1TB PCIe NVMe SSD", 1000, "NVMe SSD"),
            ("256GB NVMe M.2 SSD", 256, "NVMe SSD"),
        ]

        for text, expected_capacity, expected_type in test_cases:
            result = extractor.extract_storage(text)
            assert result is not None
            assert result["capacity_gb"] == expected_capacity
            assert result["type"] == expected_type
            assert result["confidence"] == "high"

    def test_extract_storage_standard_ssd(self):
        """Test storage extraction for standard SSDs."""
        extractor = NLPExtractor()

        result = extractor.extract_storage("512GB SSD")
        assert result is not None
        assert result["capacity_gb"] == 512
        assert result["type"] == "SSD"
        assert result["confidence"] == "high"

    def test_extract_gpu_nvidia_rtx(self):
        """Test GPU extraction for NVIDIA RTX cards."""
        extractor = NLPExtractor()

        test_cases = [
            "NVIDIA GeForce RTX 3060",
            "RTX 3060 Ti",
            "GeForce RTX 4070 SUPER",
        ]

        for text in test_cases:
            result = extractor.extract_gpu(text)
            assert result is not None
            assert "RTX" in result.value.upper()
            assert result.confidence == "high"

    def test_extract_gpu_amd_radeon(self):
        """Test GPU extraction for AMD Radeon cards."""
        extractor = NLPExtractor()

        test_cases = [
            "AMD Radeon RX 6600",
            "RX 6600 XT",
            "Radeon RX 7900 XT",
        ]

        for text in test_cases:
            result = extractor.extract_gpu(text)
            assert result is not None
            assert "RX" in result.value.upper()
            assert result.confidence == "high"

    def test_extract_all_components(self):
        """Test extracting all components from product description."""
        extractor = NLPExtractor()

        text = (
            "Beelink Mini PC Intel Core i7-12700H 12th Gen, "
            "16GB DDR4 RAM, 512GB NVMe SSD, NVIDIA GeForce RTX 3060"
        )

        results = extractor.extract_all(text)

        assert results["cpu"] is not None
        assert "i7" in results["cpu"].value.lower()

        assert results["ram"] is not None
        assert results["ram"]["capacity_gb"] == 16

        assert results["storage"] is not None
        assert results["storage"]["capacity_gb"] == 512

        assert results["gpu"] is not None
        assert "RTX" in results["gpu"].value or "3060" in results["gpu"].value


class TestCatalogMatcher:
    """Test suite for fuzzy catalog matching."""

    def test_match_cpu_exact_match(self):
        """Test CPU matching with exact name match."""
        # Create test CPU catalog
        cpus = [
            Cpu(
                id=1,
                name="Intel Core i7-12700K",
                manufacturer="Intel",
                attributes_json={},
            ),
            Cpu(
                id=2,
                name="AMD Ryzen 5 5600X",
                manufacturer="AMD",
                attributes_json={},
            ),
        ]

        matcher = CatalogMatcher(similarity_threshold=70)
        cpu, score = matcher.match_cpu("Intel Core i7-12700K", cpus)

        assert cpu is not None
        assert cpu.name == "Intel Core i7-12700K"
        assert score >= 90

    def test_match_cpu_fuzzy_match(self):
        """Test CPU matching with fuzzy name match."""
        cpus = [
            Cpu(
                id=1,
                name="Intel Core i7-12700K",
                manufacturer="Intel",
                attributes_json={"aliases": ["i7-12700K", "Core i7-12700K", "12700K"]},
            ),
        ]

        matcher = CatalogMatcher(similarity_threshold=60)

        # Test variations that should match via aliases
        test_names = ["i7-12700K", "Core i7-12700K", "i7 12700K"]

        for test_name in test_names:
            cpu, score = matcher.match_cpu(test_name, cpus)
            assert cpu is not None, f"Failed to match: {test_name}"
            assert cpu.name == "Intel Core i7-12700K"
            assert score >= 60

    def test_match_cpu_with_aliases(self):
        """Test CPU matching using aliases."""
        cpus = [
            Cpu(
                id=1,
                name="Intel Core i7-12700K",
                manufacturer="Intel",
                attributes_json={"aliases": ["i7-12700K", "12700K"]},
            ),
        ]

        matcher = CatalogMatcher(similarity_threshold=70)
        cpu, score = matcher.match_cpu("12700K", cpus)

        assert cpu is not None
        assert cpu.name == "Intel Core i7-12700K"

    def test_match_cpu_no_match(self):
        """Test CPU matching with no valid match."""
        cpus = [
            Cpu(
                id=1,
                name="Intel Core i7-12700K",
                manufacturer="Intel",
                attributes_json={},
            ),
        ]

        matcher = CatalogMatcher(similarity_threshold=70)
        cpu, score = matcher.match_cpu("AMD Ryzen 9 7950X", cpus)

        # Should not match - too different
        assert cpu is None or score < 70

    def test_match_gpu_exact_match(self):
        """Test GPU matching with exact name match."""
        gpus = [
            Gpu(
                id=1,
                name="NVIDIA GeForce RTX 3060",
                manufacturer="NVIDIA",
                attributes_json={},
            ),
        ]

        matcher = CatalogMatcher(similarity_threshold=70)
        gpu, score = matcher.match_gpu("NVIDIA GeForce RTX 3060", gpus)

        assert gpu is not None
        assert gpu.name == "NVIDIA GeForce RTX 3060"
        assert score >= 90

    def test_match_with_confidence(self):
        """Test matching with confidence levels."""
        cpus = [
            Cpu(
                id=1,
                name="Intel Core i7-12700K",
                manufacturer="Intel",
                attributes_json={"aliases": ["i7-12700K", "12700K"]},
            ),
        ]

        matcher = CatalogMatcher(similarity_threshold=60)

        # High confidence match (exact)
        result = matcher.match_cpu_with_confidence("Intel Core i7-12700K", cpus)
        assert result["confidence"] == "high"
        assert result["requires_review"] is False

        # Match via alias (should also be high confidence)
        result = matcher.match_cpu_with_confidence("i7-12700K", cpus)
        assert result["cpu"] is not None
        # Confidence depends on score

    def test_normalize_component_name(self):
        """Test component name normalization."""
        test_cases = [
            ("Intel® Core™ i7-12700K", "intel core i7-12700k"),
            ("NVIDIA GeForce RTX 3060", "nvidia geforce rtx 3060"),
            ("AMD Ryzen Processor", "amd ryzen"),
        ]

        for input_name, expected in test_cases:
            result = normalize_component_name(input_name)
            assert result == expected


class TestEndToEndWorkflow:
    """Test end-to-end Amazon import workflow."""

    @pytest.mark.asyncio
    async def test_extract_from_amazon_data(self):
        """Test component extraction from scraped Amazon data."""
        amazon_data = {
            "title": "Beelink Mini PC Intel Core i7-12700H, 16GB DDR4, 512GB NVMe SSD",
            "bullet_points": [
                "Intel Core i7-12700H Processor",
                "16GB DDR4 3200MHz RAM",
                "512GB NVMe PCIe SSD",
                "Intel Iris Xe Graphics",
            ],
            "specs": {
                "Manufacturer": "Beelink",
                "Model Number": "SEi12",
            },
        }

        results = extract_from_amazon_data(amazon_data)

        # Verify CPU extraction
        assert results["cpu"] is not None
        assert "i7" in results["cpu"].value.lower()

        # Verify RAM extraction
        assert results["ram"] is not None
        assert results["ram"]["capacity_gb"] == 16

        # Verify storage extraction
        assert results["storage"] is not None
        assert results["storage"]["capacity_gb"] == 512

    @pytest.mark.asyncio
    async def test_match_extracted_components(self):
        """Test matching extracted components to catalog."""
        # Create test catalog
        cpus = [
            Cpu(
                id=1,
                name="Intel Core i7-12700H",
                manufacturer="Intel",
                attributes_json={},
            ),
        ]

        gpus = [
            Gpu(
                id=1,
                name="Intel Iris Xe Graphics",
                manufacturer="Intel",
                attributes_json={},
            ),
        ]

        # Extract components from sample data
        amazon_data = {
            "title": "Mini PC with Intel Core i7-12700H and Iris Xe Graphics",
            "bullet_points": [],
        }

        extracted = extract_from_amazon_data(amazon_data)

        # Match to catalog
        matches = await match_extracted_components(extracted, cpus, gpus)

        assert matches["cpu_match"] is not None
        assert matches["cpu_match"]["cpu"] is not None


@pytest.mark.integration
class TestRealAmazonURLs:
    """Integration tests with real Amazon URLs.

    These tests require network access and may be skipped in CI/CD.
    Run with: pytest -m integration
    """

    # Sample Amazon product URLs for testing
    SAMPLE_URLS = [
        # Mini PCs with various configurations
        # Note: These would be real URLs in production testing
        "https://www.amazon.com/dp/B0EXAMPLE1",  # Intel i7 Mini PC
        "https://www.amazon.com/dp/B0EXAMPLE2",  # AMD Ryzen Mini PC
        "https://www.amazon.com/dp/B0EXAMPLE3",  # Intel NUC
    ]

    @pytest.mark.skip(reason="Requires real Amazon URLs and network access")
    @pytest.mark.asyncio
    async def test_import_real_urls(self):
        """Test import with real Amazon URLs.

        This test should be run manually with real Amazon product URLs
        to validate the import pipeline end-to-end.
        """
        for url in self.SAMPLE_URLS:
            # Scrape product
            data = await scrape_amazon_product(url)

            # Extract components
            extracted = extract_from_amazon_data(data)

            # Validate extraction
            assert extracted["cpu"] is not None or extracted["gpu"] is not None
            # At least some components should be extracted

    @pytest.mark.skip(reason="Manual performance test")
    @pytest.mark.asyncio
    async def test_import_performance(self):
        """Test import performance meets <500ms target.

        This test measures the time to scrape and extract from a single URL.
        """
        import time

        url = "https://www.amazon.com/dp/B0EXAMPLE1"

        start_time = time.time()
        data = await scrape_amazon_product(url)
        extracted = extract_from_amazon_data(data)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms

        # Should complete in <500ms
        assert elapsed_time < 500, f"Import took {elapsed_time}ms (target: <500ms)"
