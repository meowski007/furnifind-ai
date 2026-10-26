import re

from app.api.schemas import ExtractedFilters

CATEGORY_SYNONYMS = {
    "desk": "desks",
    "desks": "desks",
    "workstation": "desks",
    "study table": "desks",
    "writing desk": "desks",
    "chair": "chairs",
    "chairs": "chairs",
    "armchair": "chairs",
    "seating": "chairs",
    "stool": "chairs",
    "sofa": "sofas",
    "sofas": "sofas",
    "couch": "sofas",
    "daybed": "sofas",
    "sectional": "sofas",
    "futon": "sofas",
    "table": "tables",
    "tables": "tables",
    "dining table": "tables",
    "coffee table": "tables",
    "bed": "beds",
    "beds": "beds",
    "bed frame": "beds",
    "bookcase": "bookcases",
    "bookcases": "bookcases",
    "bookshelf": "bookcases",
    "bookshelves": "bookcases",
    "shelf": "storage",
    "shelves": "storage",
    "storage": "storage",
    "sideboard": "storage",
    "credenza": "storage",
    "dresser": "storage",
    "cabinet": "storage",
    "lamp": "lighting",
    "lighting": "lighting",
    "floor lamp": "lighting",
}

MATERIALS = [
    "oak",
    "walnut",
    "pine",
    "wood",
    "metal",
    "steel",
    "iron",
    "leather",
    "velvet",
    "linen",
    "fabric",
    "marble",
    "glass",
    "rattan",
    "cane",
    "bamboo",
    "brass",
    "ceramic",
    "mesh",
    "sheesham",
    "ash",
]

COLOURS = [
    "white",
    "black",
    "beige",
    "oak",
    "walnut",
    "navy blue",
    "blue",
    "emerald green",
    "green",
    "grey",
    "gray",
    "dove grey",
    "cigar brown",
    "cognac",
    "brown",
    "brass",
    "ivory",
    "natural",
]

STYLES = [
    "scandinavian",
    "scandi",
    "modern",
    "industrial",
    "mid-century",
    "minimalist",
    "rustic",
    "boho",
    "bohemian",
]


class QueryParser:
    """Deterministic extractor for furniture search constraints and residual keywords."""

    @classmethod
    def parse_query(cls, raw_query: str) -> tuple[ExtractedFilters, str]:
        q = raw_query.lower()
        extracted = ExtractedFilters()
        residual_tokens = raw_query

        # 1. Dimension extraction: width (RUN FIRST so "width below 120 cm" is not mistaken for price)
        width_patterns = [
            r"(?:width|wide)\s*(?:below|under|less\s+than|<=?)\s*([0-9]+(?:\.[0-9]+)?)\s*(?:cm|centimeters)?",
            r"narrower\s+than\s*([0-9]+(?:\.[0-9]+)?)\s*(?:cm)?",
            r"([0-9]+(?:\.[0-9]+)?)\s*(?:cm)?\s*(?:width|wide)\s*or\s*less",
        ]
        for pattern in width_patterns:
            m = re.search(pattern, q)
            if m:
                extracted.max_width_cm = float(m.group(1))
                residual_tokens = re.sub(pattern, " ", residual_tokens, flags=re.IGNORECASE)
                # Also update q so price patterns don't re-match the same number
                q = re.sub(pattern, " ", q)
                break

        # 2. Price extraction (e.g., "under 15000", "below ₹12,000", "budget 20000")
        price_patterns = [
            r"(?:under|below|less\s+than|budget(?:\s+of)?|max(?:imum)?\s+price|up\s+to)\s*(?:₹|rs\.?|inr)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?|\d+k)(?!\s*cm\b)",
            r"(?:₹|rs\.?|inr)\s*([0-9]+(?:,[0-9]+)*)\s*(?:or\s+less|max)",
        ]
        for pattern in price_patterns:
            m = re.search(pattern, q)
            if m:
                val_str = m.group(1).replace(",", "")
                if val_str.endswith("k"):
                    max_p = float(val_str[:-1]) * 1000
                else:
                    max_p = float(val_str)
                extracted.max_price = max_p
                residual_tokens = re.sub(pattern, " ", residual_tokens, flags=re.IGNORECASE)
                q = re.sub(pattern, " ", q)
                break

        # Min price extraction (e.g. "above 5000", "min 10000")
        min_price_patterns = [
            r"(?:above|more\s+than|min(?:imum)?\s+price|at\s+least)\s*(?:₹|rs\.?|inr)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?|\d+k)(?!\s*cm\b)",
        ]
        for pattern in min_price_patterns:
            m = re.search(pattern, q)
            if m:
                val_str = m.group(1).replace(",", "")
                if val_str.endswith("k"):
                    min_p = float(val_str[:-1]) * 1000
                else:
                    min_p = float(val_str)
                extracted.min_price = min_p
                residual_tokens = re.sub(pattern, " ", residual_tokens, flags=re.IGNORECASE)
                q = re.sub(pattern, " ", q)
                break

        # 3. Category extraction
        # Sort keys by length descending to match composite phrases like "dining table" before "table"
        sorted_cat_keys = sorted(CATEGORY_SYNONYMS.keys(), key=len, reverse=True)
        for cat_term in sorted_cat_keys:
            pattern = rf"\b{re.escape(cat_term)}\b"
            if re.search(pattern, q):
                extracted.category = CATEGORY_SYNONYMS[cat_term]
                # Keep category term in residual for semantic context, but noted in filter
                break

        # 4. Style extraction
        for style in STYLES:
            pattern = rf"\b{re.escape(style)}\b"
            if re.search(pattern, q):
                extracted.style = (
                    "scandinavian"
                    if style == "scandi"
                    else ("boho" if style == "bohemian" else style)
                )
                break

        # 5. Material extraction
        for mat in MATERIALS:
            pattern = rf"\b{re.escape(mat)}\b"
            if re.search(pattern, q):
                extracted.material = mat
                break

        # 6. Colour extraction
        # Check longer colours first (e.g. "emerald green", "navy blue", "dove grey", "cigar brown")
        sorted_colours = sorted(COLOURS, key=len, reverse=True)
        for col in sorted_colours:
            pattern = rf"\b{re.escape(col)}\b"
            if re.search(pattern, q):
                # Don't accidentally treat material "oak" as colour if already picked material
                if col == "oak" and extracted.material == "oak":
                    continue
                extracted.colour = col
                break

        # Clean up residual query
        residual = re.sub(r"\s+", " ", residual_tokens).strip()
        if not residual:
            residual = raw_query.strip()

        return extracted, residual
