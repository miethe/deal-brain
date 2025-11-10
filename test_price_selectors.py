#!/usr/bin/env python3
"""
Test price selector priority to identify why extraction is failing
"""

from bs4 import BeautifulSoup

html_file = "/mnt/containers/deal-brain/debug_amazon.com_1fe23618.html"

with open(html_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'html.parser')

print("=" * 80)
print("TESTING PRICE SELECTOR PRIORITY")
print("=" * 80)

# Test each selector in priority order
selectors = [
    ("Priority 1", "#corePriceDisplay_desktop_feature_div span.a-offscreen"),
    ("Priority 2", "span.a-price > span.a-offscreen"),
    ("Priority 3a", "span.a-price span.a-price-whole span.a-offscreen"),
    ("Priority 3b", "span.priceToPay span.a-offscreen"),
    ("Priority 4", "#price_inside_buybox"),
    ("Priority 5a", "#priceblock_ourprice"),
    ("Priority 5b", "#priceblock_dealprice"),
    ("Priority 6", ".a-price span[aria-hidden='true']"),
]

for label, selector in selectors:
    print(f"\n{label}: {selector}")
    print("-" * 80)

    elements = soup.select(selector)
    print(f"Found {len(elements)} elements")

    for i, elem in enumerate(elements[:5]):  # Show first 5
        text = elem.get_text(strip=True)
        if text:
            print(f"  [{i}] '{text}'")
        else:
            print(f"  [{i}] <EMPTY>")

        # Show parent context
        parent = elem.parent
        if parent:
            parent_classes = parent.get('class', [])
            parent_id = parent.get('id', '')
            print(f"      Parent: {parent.name} class={parent_classes} id={parent_id}")

# Test the specific working selector
print("\n" + "=" * 80)
print("RECOMMENDED WORKING SELECTOR")
print("=" * 80)
working = soup.select_one("span.priceToPay span.a-offscreen")
if working:
    print(f"✓ span.priceToPay span.a-offscreen: '{working.get_text(strip=True)}'")
else:
    print("✗ Not found")

# Check if corePriceDisplay contains priceToPay
core_div = soup.find(id="corePriceDisplay_desktop_feature_div")
if core_div:
    print(f"\n✓ #corePriceDisplay_desktop_feature_div exists")
    price_to_pay = core_div.find('span', class_='priceToPay')
    if price_to_pay:
        print(f"  ✓ Contains span.priceToPay")
        offscreen = price_to_pay.find('span', class_='a-offscreen')
        if offscreen:
            print(f"    ✓ Contains span.a-offscreen: '{offscreen.get_text(strip=True)}'")
        else:
            print(f"    ✗ No a-offscreen inside priceToPay")
    else:
        print(f"  ✗ No span.priceToPay found")

    # Show all a-offscreen in corePriceDisplay
    all_offscreen = core_div.find_all('span', class_='a-offscreen')
    print(f"  All a-offscreen in corePriceDisplay ({len(all_offscreen)}):")
    for i, elem in enumerate(all_offscreen):
        text = elem.get_text(strip=True)
        parent_classes = elem.parent.get('class', []) if elem.parent else []
        print(f"    [{i}] '{text}' (parent classes: {parent_classes})")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("The selector #corePriceDisplay_desktop_feature_div span.a-offscreen")
print("is too broad and catches multiple elements including empty ones.")
print("\nRECOMMENDED FIX:")
print("1. Move 'span.priceToPay span.a-offscreen' to Priority 1")
print("2. Or use '#corePriceDisplay_desktop_feature_div span.priceToPay span.a-offscreen'")
print("=" * 80)
