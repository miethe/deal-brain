#!/usr/bin/env python3
"""
Find the actual working selector for $299.00 price
"""

from bs4 import BeautifulSoup
import re

html_file = "/mnt/containers/deal-brain/debug_amazon.com_1fe23618.html"

with open(html_file, "r", encoding="utf-8") as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, "html.parser")

print("=" * 80)
print("FINDING WORKING SELECTOR FOR $299.00")
print("=" * 80)


# Look for elements containing exactly "$299.00" (not list price)
def extract_price(text):
    """Extract first price from text"""
    match = re.search(r"\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)", text)
    return match.group(0) if match else None


# Test 1: aok-offscreen (NOT a-offscreen)
print("\n1. Testing 'aok-offscreen' class (Amazon's screen reader text)")
print("-" * 80)
aok_offscreen = soup.find_all(class_="aok-offscreen")
for elem in aok_offscreen:
    text = elem.get_text(strip=True)
    if "$299" in text and "savings" in text.lower():
        print(f"✓ FOUND: '{text}'")
        print(f"  Selector: span.aok-offscreen")
        print(f"  Parent: {elem.parent.name if elem.parent else 'N/A'}")
        # Show parent context
        if elem.parent:
            parent_id = elem.parent.get("id", "")
            parent_class = elem.parent.get("class", [])
            print(f"  Parent ID: {parent_id}")
            print(f"  Parent classes: {parent_class}")
        break

# Test 2: aria-hidden spans with price fragments
print("\n2. Testing 'aria-hidden' price fragments")
print("-" * 80)
aria_hidden = soup.find_all("span", {"aria-hidden": "true"})
for elem in aria_hidden:
    # Check if this is a priceToPay parent
    parent = elem.parent
    if parent and "priceToPay" in parent.get("class", []):
        text = elem.get_text(strip=True)
        if "299" in text:
            print(f"✓ FOUND: '{text}'")
            print(f"  Selector: span.priceToPay > span[aria-hidden='true']")
            print(f"  Or: .a-price span[aria-hidden='true']")
            # Parse the fragments
            symbol = elem.find("span", class_="a-price-symbol")
            whole = elem.find("span", class_="a-price-whole")
            fraction = elem.find("span", class_="a-price-fraction")
            if symbol and whole and fraction:
                price = f"{symbol.get_text(strip=True)}{whole.get_text(strip=True)}{fraction.get_text(strip=True)}"
                print(f"  Reconstructed price: {price}")
            break

# Test 3: Check corePriceDisplay specifically
print("\n3. Testing within corePriceDisplay_desktop_feature_div")
print("-" * 80)
core_div = soup.find(id="corePriceDisplay_desktop_feature_div")
if core_div:
    # Try aok-offscreen first
    aok = core_div.find("span", class_="aok-offscreen")
    if aok:
        text = aok.get_text(strip=True)
        if "$299" in text:
            print(f"✓ FOUND via aok-offscreen: '{text}'")
            print(f"  Selector: #corePriceDisplay_desktop_feature_div span.aok-offscreen")

    # Try priceToPay + aria-hidden
    price_to_pay = core_div.find("span", class_="priceToPay")
    if price_to_pay:
        aria = price_to_pay.find("span", {"aria-hidden": "true"})
        if aria:
            text = aria.get_text(strip=True)
            print(f"✓ FOUND via priceToPay aria-hidden: '{text}'")
            print(
                f"  Selector: #corePriceDisplay_desktop_feature_div span.priceToPay span[aria-hidden='true']"
            )

# Test 4: Generic span.a-price > span.a-offscreen (first occurrence)
print("\n4. Testing 'span.a-price > span.a-offscreen' (FIRST match)")
print("-" * 80)
first_match = soup.select_one("span.a-price > span.a-offscreen")
if first_match:
    text = first_match.get_text(strip=True)
    print(f"Result: '{text}'")
    if text:
        print(f"✓ This selector works!")
    else:
        print(f"✗ Empty result - this is the bug!")
        print(f"  Need to find a-price WITHOUT priceToPay")

        # Find all a-price > a-offscreen and show which ones have content
        all_matches = soup.select("span.a-price > span.a-offscreen")
        print(f"\n  All {len(all_matches)} matches:")
        for i, match in enumerate(all_matches[:5]):
            text = match.get_text(strip=True)
            parent_class = match.parent.get("class", [])
            has_price_to_pay = "priceToPay" in parent_class
            print(
                f"    [{i}] '{text}' (parent classes: {parent_class}) {'← priceToPay' if has_price_to_pay else ''}"
            )

print("\n" + "=" * 80)
print("RECOMMENDED FIX")
print("=" * 80)
print("OPTION 1 (Best): Use aok-offscreen in corePriceDisplay")
print("  #corePriceDisplay_desktop_feature_div span.aok-offscreen")
print("")
print("OPTION 2: Use aria-hidden and reconstruct price from fragments")
print("  #corePriceDisplay_desktop_feature_div span.priceToPay span[aria-hidden='true']")
print("")
print("OPTION 3: Filter span.a-price > span.a-offscreen to exclude priceToPay")
print("  span.a-price:not(.priceToPay) > span.a-offscreen")
print("=" * 80)
