"""Generate sample product placeholder images for local development and visual testing."""

import json
from pathlib import Path

from PIL import Image, ImageDraw

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CATALOGUE_PATH = DATA_DIR / "sample_catalogue.json"
IMAGES_DIR = DATA_DIR / "images"

CATEGORY_PALETTES = {
    "desks": ("#f5ebe0", "#d5bdaf", "#6b4f3a"),
    "chairs": ("#e0ecf5", "#b8d0eb", "#2b4c7e"),
    "sofas": ("#eae4e9", "#dfd7df", "#5c4d61"),
    "tables": ("#e8eddf", "#cfdbd5", "#333d29"),
    "beds": ("#f0ead6", "#ddc3a5", "#473c35"),
    "bookcases": ("#ede0d4", "#ddb892", "#7f5539"),
    "storage": ("#e6e8e6", "#ced4da", "#343a40"),
    "lighting": ("#fff1e6", "#fde2e4", "#c97a7e"),
}


def generate_images():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    with open(CATALOGUE_PATH, "r", encoding="utf-8") as f:
        products = json.load(f)

    for item in products:
        product_id = item["product_id"]
        title = item["title"]
        category = item.get("category", "desks")
        bg_col, accent_col, text_col = CATEGORY_PALETTES.get(
            category, ("#f4f4f4", "#e0e0e0", "#333333")
        )

        # Create 400x300 image
        img = Image.new("RGB", (400, 300), color=bg_col)
        draw = ImageDraw.Draw(img)

        # Draw decorative furniture frame box
        draw.rectangle([20, 20, 380, 280], outline=accent_col, width=4)
        draw.rectangle([35, 35, 365, 265], fill=accent_col)

        # Draw inner card
        draw.rectangle([50, 60, 350, 240], fill="#ffffff", outline=text_col, width=2)

        # Text labels
        draw.text((70, 80), "FurniFind AI", fill=text_col)
        draw.text((70, 110), f"[{category.upper()}]", fill=text_col)

        # Draw wrapped title lines
        words = title.split()
        line1 = " ".join(words[:4])
        line2 = " ".join(words[4:8]) if len(words) > 4 else ""
        draw.text((70, 140), line1, fill=text_col)
        if line2:
            draw.text((70, 165), line2, fill=text_col)

        draw.text((70, 200), f"ID: {product_id} | ₹{item['price']:,.0f}", fill=text_col)

        out_path = IMAGES_DIR / f"{product_id}.png"
        img.save(out_path, format="PNG")

    print(f"Generated {len(products)} images in {IMAGES_DIR}")


if __name__ == "__main__":
    generate_images()
