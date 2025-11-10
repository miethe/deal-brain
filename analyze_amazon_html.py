#!/usr/bin/env python3
"""
Analyze Amazon product HTML to identify correct extraction selectors
"""

from bs4 import BeautifulSoup
import re
import json

html_file = "/mnt/containers/deal-brain/debug_amazon.com_1fe23618.html"

with open(html_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'html.parser')

print("=" * 80)
print("AMAZON PRODUCT HTML ANALYSIS")
print("=" * 80)

# 1. TITLE EXTRACTION
print("\n1. TITLE EXTRACTION")
print("-" * 80)
title_elem = soup.find(id="productTitle")
if title_elem:
    title_text = title_elem.get_text(strip=True)
    print(f"✓ Found #productTitle: {title_text[:100]}...")
    print(f"  Selector: #productTitle")
else:
    print("✗ #productTitle not found")

# 2. PRICE EXTRACTION - Look for $299
print("\n2. PRICE EXTRACTION ($299 Deal Price)")
print("-" * 80)

# Method 1: Check corePriceDisplay
core_price = soup.find(id="corePriceDisplay_desktop_feature_div")
if core_price:
    print("✓ Found #corePriceDisplay_desktop_feature_div")

    # Look for priceToPay
    price_to_pay = core_price.find('span', class_='priceToPay')
    if price_to_pay:
        offscreen = price_to_pay.find('span', class_='a-offscreen')
        if offscreen:
            price_text = offscreen.get_text(strip=True)
            print(f"  ✓ Found span.priceToPay > span.a-offscreen: {price_text}")
            print(f"    Selector: #corePriceDisplay_desktop_feature_div span.priceToPay span.a-offscreen")
            print(f"    Alternative: span.priceToPay span.a-offscreen")

    # Check for savings percentage
    savings = core_price.find('span', class_='savingsPercentage')
    if savings:
        print(f"  ✓ Found savings: {savings.get_text(strip=True)}")

# Method 2: Check tp_price_block_total_price_ww
tp_price = soup.find(id="tp_price_block_total_price_ww")
if tp_price:
    offscreen = tp_price.find('span', class_='a-offscreen')
    if offscreen:
        price_text = offscreen.get_text(strip=True)
        print(f"✓ Found #tp_price_block_total_price_ww span.a-offscreen: {price_text}")
        print(f"  Selector: #tp_price_block_total_price_ww span.a-offscreen")

# Method 3: Generic a-price searches
all_prices = soup.find_all('span', class_='a-offscreen')
prices_found = []
for price_elem in all_prices:
    text = price_elem.get_text(strip=True)
    if '$' in text and text not in prices_found:
        prices_found.append(text)

print(f"\n  All a-offscreen prices found: {prices_found[:10]}")

# 3. LIST PRICE ($419 from screenshot context, not $699)
print("\n3. LIST PRICE (Crossed Out)")
print("-" * 80)
basis_price = soup.find('span', class_='basisPrice')
if basis_price:
    price_elem = basis_price.find('span', class_='a-price')
    if price_elem:
        offscreen = price_elem.find('span', class_='a-offscreen')
        if offscreen:
            list_price = offscreen.get_text(strip=True)
            print(f"✓ Found span.basisPrice span.a-price span.a-offscreen: {list_price}")
            print(f"  Selector: span.basisPrice span.a-offscreen")

# 4. BRAND
print("\n4. BRAND/MANUFACTURER")
print("-" * 80)
byline = soup.find(id="bylineInfo")
if byline:
    brand_text = byline.get_text(strip=True)
    print(f"✓ Found #bylineInfo: {brand_text}")
    print(f"  Selector: #bylineInfo")

    # Extract just "Beelink" from "Visit the Beelink Store"
    match = re.search(r'Visit the (.+?) Store', brand_text)
    if match:
        print(f"  Extracted brand: {match.group(1)}")

# Check product details table
prod_details = soup.find('table', class_='prodDetTable')
if prod_details:
    brand_row = prod_details.find('th', string=re.compile(r'Brand', re.I))
    if brand_row:
        brand_td = brand_row.find_next_sibling('td')
        if brand_td:
            print(f"✓ Found in prodDetTable: {brand_td.get_text(strip=True)}")
            print(f"  Selector: table.prodDetTable th:contains('Brand') + td")

# 5. SPECS EXTRACTION
print("\n5. SPECIFICATIONS (CPU, RAM, Storage)")
print("-" * 80)

# From product details table
if prod_details:
    print("✓ Found product details table (table.prodDetTable)")

    # Extract key specs
    specs = {}
    for row in prod_details.find_all('tr'):
        th = row.find('th')
        td = row.find('td')
        if th and td:
            key = th.get_text(strip=True)
            value = td.get_text(strip=True)
            specs[key] = value

    # Print relevant specs
    relevant_keys = ['Processor', 'RAM', 'Hard Drive', 'Brand', 'Series', 'Item model number']
    for key in relevant_keys:
        if key in specs:
            print(f"  • {key}: {specs[key]}")

# 6. IMAGES
print("\n6. PRODUCT IMAGES")
print("-" * 80)
img_wrapper = soup.find(id="imgTagWrapperId")
if img_wrapper:
    img = img_wrapper.find('img')
    if img:
        print(f"✓ Found main image in #imgTagWrapperId")

        # Check for high-res image
        if img.get('data-old-hires'):
            print(f"  • data-old-hires: {img['data-old-hires'][:80]}...")

        if img.get('data-a-dynamic-image'):
            print(f"  • data-a-dynamic-image found (JSON with multiple sizes)")
            try:
                dynamic = json.loads(img['data-a-dynamic-image'])
                urls = list(dynamic.keys())
                print(f"  • Available image URLs: {len(urls)}")
                if urls:
                    print(f"  • Highest res: {urls[0][:80]}...")
            except:
                pass

        if img.get('src'):
            print(f"  • src: {img['src'][:80]}...")

# 7. ASIN
print("\n7. ASIN")
print("-" * 80)
asin_elem = soup.find('th', string=re.compile(r'ASIN', re.I))
if asin_elem:
    asin_td = asin_elem.find_next_sibling('td')
    if asin_td:
        print(f"✓ Found ASIN: {asin_td.get_text(strip=True)}")
        print(f"  Selector: Look for 'ASIN' in product details table")

# SUMMARY
print("\n" + "=" * 80)
print("CRITICAL FINDINGS SUMMARY")
print("=" * 80)

print("\n✓ WORKING SELECTORS:")
print("  1. Title: #productTitle")
print("  2. Price: span.priceToPay span.a-offscreen")
print("  3. List Price: span.basisPrice span.a-offscreen")
print("  4. Brand: #bylineInfo (need regex to extract)")
print("  5. Specs: table.prodDetTable (structured data)")
print("  6. Images: #imgTagWrapperId img[data-old-hires] or [data-a-dynamic-image]")

print("\n✗ WHY CURRENT LOGIC MAY FAIL:")
print("  1. corePriceDisplay_desktop_feature_div is correct but needs priceToPay class")
print("  2. Missing span.priceToPay in current selector list")
print("  3. Need to prioritize corePriceDisplay over generic span.a-price")

print("\n" + "=" * 80)
