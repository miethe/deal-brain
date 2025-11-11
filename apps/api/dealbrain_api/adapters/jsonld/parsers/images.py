"""Image extraction utilities for product images."""

import json
from typing import Any

from bs4 import BeautifulSoup


class ImageParser:
    """
    Extracts image URLs from various sources.

    Supports:
    - Schema.org Product image fields
    - Amazon data-old-hires and data-a-dynamic-image attributes
    - Generic img tags with fallback logic
    """

    @staticmethod
    def extract_images_from_product(product: dict[str, Any]) -> list[str]:
        """
        Extract image URLs from Schema.org Product data.

        Product may have:
        - image: "url" (single string)
        - image: ["url1", "url2"] (list)
        - images: ["url1", "url2"] (list)

        Args:
            product: Product schema dict

        Returns:
            List of image URLs (primary image only)
        """
        image_data = product.get("image") or product.get("images", [])

        if isinstance(image_data, str):
            return [image_data] if image_data else []
        elif isinstance(image_data, list):
            # Return first valid URL only
            for item in image_data:
                if isinstance(item, str):
                    return [item]
                elif isinstance(item, dict) and "url" in item:
                    return [item["url"]]
            return []
        elif isinstance(image_data, dict) and "url" in image_data:
            return [image_data["url"]]

        return []

    @staticmethod
    def extract_images_from_html(soup: BeautifulSoup) -> list[str]:
        """
        Extract high-resolution product images from Amazon product gallery.

        Extraction methods (in order):
        1. img[data-old-hires] attribute - High-res direct URLs
        2. img[data-a-dynamic-image] attribute - JSON-encoded URL map

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List of up to 5 image URLs (all starting with "http")
        """
        images: list[str] = []

        # Primary method: data-old-hires attribute (high-res)
        image_elements = soup.select("img[data-old-hires]")
        if not image_elements:
            # Fallback: data-a-dynamic-image attribute
            image_elements = soup.select("img[data-a-dynamic-image]")

        for img in image_elements:
            # Extract from data-old-hires attribute
            if img.has_attr("data-old-hires"):
                url = img.get("data-old-hires", "")
                url_str = url if isinstance(url, str) else str(url) if url else ""
                if url_str and url_str.startswith("http"):
                    images.append(url_str)
            # Extract from data-a-dynamic-image attribute (JSON encoded)
            elif img.has_attr("data-a-dynamic-image"):
                try:
                    dynamic_attr = img.get("data-a-dynamic-image", "{}")
                    dynamic_str = (
                        dynamic_attr
                        if isinstance(dynamic_attr, str)
                        else str(dynamic_attr)
                        if dynamic_attr
                        else "{}"
                    )
                    dynamic_data = json.loads(dynamic_str)
                    # Keys are image URLs, values are dimensions
                    for img_url in dynamic_data.keys():
                        if img_url.startswith("http"):
                            images.append(img_url)
                            break  # Take first/largest image
                except (json.JSONDecodeError, AttributeError):
                    pass

            # Limit to 5 images
            if len(images) >= 5:
                break

        return images[:5]


__all__ = ["ImageParser"]
