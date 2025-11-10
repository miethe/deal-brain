#!/usr/bin/env python3
"""
Debug HTML Fetching for URL Ingestion

This script fetches HTML content from a URL using the exact same httpx client
configuration as the ingestion service's JsonLdAdapter. This allows you to
inspect the actual HTML that the adapter receives and debug extraction issues.

USAGE:
------

Basic usage (fetches Amazon URL and saves to debug_amazon.html):
    poetry run python scripts/development/debug_fetch_html.py "https://www.amazon.com/dp/B0FD3BCMBS?th=1"

Custom output file:
    poetry run python scripts/development/debug_fetch_html.py "https://www.amazon.com/dp/B0FD3BCMBS?th=1" custom_output.html

Output directory (saves with auto-generated filename):
    poetry run python scripts/development/debug_fetch_html.py "https://www.amazon.com/dp/B0FD3BCMBS?th=1" --output-dir /tmp/debug

EXAMPLES:
---------

1. Debug Amazon price extraction:
    poetry run python scripts/development/debug_fetch_html.py "https://www.amazon.com/dp/B0FD3BCMBS"

2. Debug eBay listing extraction:
    poetry run python scripts/development/debug_fetch_html.py "https://www.ebay.com/itm/123456789"

3. Save to specific location:
    poetry run python scripts/development/debug_fetch_html.py "https://example.com/product" /tmp/example.html

WHAT IT DOES:
-------------

1. Fetches HTML using httpx.AsyncClient with identical configuration to production:
   - Same User-Agent header
   - Same Accept headers
   - Same timeout (8 seconds)
   - Same redirect following behavior

2. Saves the raw HTML to a file for inspection

3. Shows diagnostic information:
   - HTTP status code
   - Content length
   - Whether key HTML elements exist (title, price selectors, product ID)
   - Count of common Amazon/eBay element patterns

4. Allows you to analyze the exact HTML that the adapter sees, which is crucial
   for debugging extraction logic, especially when:
   - Price extraction fails
   - Title extraction returns generic site names
   - Structured data (JSON-LD) is missing
   - HTML element selectors don't match

WHY USE THIS:
-------------

When debugging import failures, you need to see the EXACT HTML that the ingestion
service receives. This script replicates the production fetch behavior so you can:

- Verify which HTML elements actually exist on the page
- Test CSS selectors locally before updating adapter code
- Compare Amazon's HTML structure across different product pages
- Understand why certain extractions fail
- Avoid getting different HTML due to different User-Agent or headers

RELATED FILES:
--------------

- apps/api/dealbrain_api/adapters/jsonld.py:224-297  (_fetch_html method)
- apps/api/dealbrain_api/adapters/base.py           (Base adapter configuration)

SEE ALSO:
---------

After fetching HTML, you can analyze it with BeautifulSoup:

    from bs4 import BeautifulSoup
    html = open('debug_amazon.html').read()
    soup = BeautifulSoup(html, 'html.parser')

    # Test price selectors
    soup.select_one('#corePriceDisplay_desktop_feature_div span.a-offscreen')
    soup.select_one('span.a-price span.a-offscreen')
    soup.select_one('#price_inside_buybox')

    # Test title selectors
    soup.select_one('#productTitle')
    soup.select_one('h1')
"""

import argparse
import asyncio
import hashlib
import sys
from pathlib import Path

import httpx


async def fetch_html(url: str, output_file: str) -> dict:
    """
    Fetch HTML from URL using production ingestion configuration.

    Args:
        url: URL to fetch
        output_file: Path to save HTML content

    Returns:
        Dictionary with fetch results and diagnostics
    """
    # Headers match JsonLdAdapter._fetch_html() exactly
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Timeout matches adapter default
    timeout = 8

    try:
        # Use identical client configuration as production
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            html = response.text

            # Save HTML to file
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding="utf-8")

            # Extract diagnostics
            diagnostics = {
                "url": url,
                "status_code": response.status_code,
                "content_length": len(html),
                "output_file": str(output_path.absolute()),
                "headers": dict(response.headers),
                # HTML structure analysis
                "has_title_tag": "<title>" in html,
                "title_content": _extract_between(html, "<title>", "</title>"),
                "has_productTitle": 'id="productTitle"' in html,
                "has_price_elements": html.count('class="a-price"'),
                "has_corePriceDisplay": "corePriceDisplay" in html,
                "has_price_inside_buybox": "price_inside_buybox" in html,
                "has_meta_tags": html.count("<meta"),
                "has_jsonld": 'type="application/ld+json"' in html,
                # Additional patterns
                "has_ebay_patterns": "ebay" in html.lower(),
                "has_amazon_patterns": "amazon" in html.lower(),
            }

            return diagnostics

    except httpx.TimeoutException as e:
        return {
            "error": "timeout",
            "message": f"Request timed out after {timeout}s",
            "exception": str(e),
        }
    except httpx.NetworkError as e:
        return {
            "error": "network",
            "message": "Network error occurred",
            "exception": str(e),
        }
    except Exception as e:
        return {
            "error": "unknown",
            "message": "Unexpected error occurred",
            "exception": str(e),
        }


def _extract_between(text: str, start: str, end: str) -> str:
    """Extract text between two markers."""
    try:
        start_idx = text.find(start)
        if start_idx == -1:
            return "NOT_FOUND"
        start_idx += len(start)
        end_idx = text.find(end, start_idx)
        if end_idx == -1:
            return "NOT_FOUND"
        content = text[start_idx:end_idx].strip()
        return content[:100] + "..." if len(content) > 100 else content
    except Exception:
        return "ERROR"


def _generate_output_filename(url: str) -> str:
    """Generate output filename from URL."""
    # Extract domain
    domain = url.split("//")[-1].split("/")[0].replace("www.", "")

    # Hash the URL for uniqueness
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

    return f"debug_{domain}_{url_hash}.html"


def print_diagnostics(diagnostics: dict) -> None:
    """Print diagnostic information in a formatted way."""
    if "error" in diagnostics:
        print("\n❌ FETCH FAILED")
        print("=" * 80)
        print(f"Error Type: {diagnostics['error']}")
        print(f"Message: {diagnostics['message']}")
        print(f"Exception: {diagnostics['exception']}")
        return

    print("\n✅ FETCH SUCCESSFUL")
    print("=" * 80)
    print(f"URL: {diagnostics['url']}")
    print(f"Status Code: {diagnostics['status_code']}")
    print(f"Content Length: {diagnostics['content_length']:,} characters")
    print(f"Output File: {diagnostics['output_file']}")

    print("\n📊 HTML STRUCTURE ANALYSIS")
    print("=" * 80)
    print(f"Title Tag: {'✓' if diagnostics['has_title_tag'] else '✗'}")
    print(f"  Content: {diagnostics['title_content']}")
    print(f"\nAmazon Patterns: {'✓' if diagnostics['has_amazon_patterns'] else '✗'}")
    print(f"  #productTitle: {'✓' if diagnostics['has_productTitle'] else '✗'}")
    print(f"  .a-price elements: {diagnostics['has_price_elements']}")
    print(f"  #corePriceDisplay: {'✓' if diagnostics['has_corePriceDisplay'] else '✗'}")
    print(f"  #price_inside_buybox: {'✓' if diagnostics['has_price_inside_buybox'] else '✗'}")
    print(f"\neBay Patterns: {'✓' if diagnostics['has_ebay_patterns'] else '✗'}")

    print(f"\nStructured Data:")
    print(f"  Meta tags: {diagnostics['has_meta_tags']}")
    print(f"  JSON-LD: {'✓' if diagnostics['has_jsonld'] else '✗'}")

    print("\n💡 NEXT STEPS")
    print("=" * 80)
    print(f"1. Open HTML file: {diagnostics['output_file']}")
    print("2. Search for price elements to validate selectors")
    print("3. Compare against adapter extraction logic:")
    print("   apps/api/dealbrain_api/adapters/jsonld.py")
    print("\nTo analyze with BeautifulSoup:")
    print(f"  from bs4 import BeautifulSoup")
    print(f"  html = open('{diagnostics['output_file']}').read()")
    print(f"  soup = BeautifulSoup(html, 'html.parser')")
    print(f"  soup.select_one('#productTitle')")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch HTML using production ingestion configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("url", help="URL to fetch HTML from")

    parser.add_argument(
        "output",
        nargs="?",
        help="Output file path (default: auto-generated from URL)",
    )

    parser.add_argument(
        "--output-dir",
        help="Output directory (uses auto-generated filename)",
    )

    args = parser.parse_args()

    # Determine output file
    if args.output:
        output_file = args.output
    elif args.output_dir:
        output_file = str(Path(args.output_dir) / _generate_output_filename(args.url))
    else:
        output_file = _generate_output_filename(args.url)

    # Fetch HTML
    print(f"Fetching HTML from: {args.url}")
    print(f"Output file: {output_file}")
    print("Using production httpx configuration...")

    diagnostics = asyncio.run(fetch_html(args.url, output_file))
    print_diagnostics(diagnostics)

    # Exit with error code if fetch failed
    if "error" in diagnostics:
        sys.exit(1)


if __name__ == "__main__":
    main()
