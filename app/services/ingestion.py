import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.product import Product


class IngestionReport:
    def __init__(self):
        self.total_rows_read: int = 0
        self.valid_records_loaded: int = 0
        self.duplicates_skipped: int = 0
        self.invalid_rows: list[dict[str, Any]] = []
        self.errors: list[str] = []
        self.categories_found: dict[str, int] = {}
        self.started_at: str = datetime.utcnow().isoformat()
        self.finished_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_rows_read": self.total_rows_read,
            "valid_records_loaded": self.valid_records_loaded,
            "duplicates_skipped": self.duplicates_skipped,
            "invalid_rows_count": len(self.invalid_rows),
            "invalid_rows": self.invalid_rows,
            "errors": self.errors,
            "categories_found": self.categories_found,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class IngestionPipeline:
    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def normalize_str(val: str | None) -> str | None:
        if val is None:
            return None
        cleaned = str(val).strip()
        return cleaned.lower() if cleaned else None

    @staticmethod
    def validate_and_normalize_row(
        row: dict[str, Any], idx: int
    ) -> tuple[dict[str, Any] | None, str | None]:
        # 1. Required fields
        for req in ["product_id", "title", "category", "price"]:
            if req not in row or row[req] is None or str(row[req]).strip() == "":
                return None, f"Missing required field: {req} at record index {idx}"

        # 2. Price validation
        try:
            price = float(row["price"])
            if price <= 0:
                return None, f"Invalid price <= 0: {price} at record index {idx}"
        except (ValueError, TypeError):
            return None, f"Non-numeric price: {row.get('price')} at record index {idx}"

        # 3. Dimensions validation (optional, must be positive if present)
        dimensions = {}
        for dim in ["width", "height", "depth"]:
            val = row.get(dim)
            if val is not None and str(val).strip() != "":
                try:
                    num_val = float(val)
                    if num_val <= 0:
                        return None, f"Dimension {dim} must be > 0, got {num_val}"
                    dimensions[dim] = num_val
                except (ValueError, TypeError):
                    return None, f"Non-numeric dimension for {dim}: {val}"
            else:
                dimensions[dim] = None

        # 4. Normalized fields
        normalized = {
            "product_id": str(row["product_id"]).strip().upper(),
            "title": str(row["title"]).strip(),
            "description": str(row.get("description", "")).strip(),
            "category": str(row["category"]).strip().lower(),
            "price": price,
            "currency": str(row.get("currency", "INR")).strip().upper(),
            "material": IngestionPipeline.normalize_str(row.get("material")),
            "colour": IngestionPipeline.normalize_str(row.get("colour")),
            "style": IngestionPipeline.normalize_str(row.get("style")),
            "width": dimensions["width"],
            "height": dimensions["height"],
            "depth": dimensions["depth"],
            "image_path": str(row.get("image_path", "")).strip() or None,
            "image_url": str(row.get("image_url", "")).strip() or None,
            "availability": bool(row.get("availability", True)),
            "source": str(row.get("source", "furnifind_catalogue")).strip(),
        }
        return normalized, None

    def ingest_file(
        self, file_path: Path, force_reload: bool = False
    ) -> IngestionReport:
        report = IngestionReport()
        if not file_path.exists():
            report.errors.append(f"Catalogue file not found: {file_path}")
            report.finished_at = datetime.utcnow().isoformat()
            return report

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            report.errors.append(f"JSON parsing error in {file_path}: {e!s}")
            report.finished_at = datetime.utcnow().isoformat()
            return report

        if not isinstance(data, list):
            report.errors.append(f"Expected list of products in JSON, got {type(data)}")
            report.finished_at = datetime.utcnow().isoformat()
            return report

        report.total_rows_read = len(data)

        if force_reload:
            logger.info("force_reload is enabled: clearing existing products table")
            self.session.execute(delete(Product))
            self.session.commit()

        seen_ids = set()
        # Fetch existing IDs in database if not force_reload
        existing_res = self.session.execute(select(Product.product_id))
        db_existing_ids = set(existing_res.scalars().all())

        valid_products_to_add = []

        for idx, row in enumerate(data):
            if not isinstance(row, dict):
                report.invalid_rows.append(
                    {"index": idx, "row": row, "reason": "Item is not a JSON object"}
                )
                continue

            cleaned, err = self.validate_and_normalize_row(row, idx)
            if err:
                report.invalid_rows.append({"index": idx, "row": row, "reason": err})
                continue

            pid = cleaned["product_id"]
            if pid in seen_ids or pid in db_existing_ids:
                report.duplicates_skipped += 1
                continue

            seen_ids.add(pid)
            cat = cleaned["category"]
            report.categories_found[cat] = report.categories_found.get(cat, 0) + 1

            product_obj = Product(
                product_id=cleaned["product_id"],
                title=cleaned["title"],
                description=cleaned["description"],
                category=cleaned["category"],
                price=cleaned["price"],
                currency=cleaned["currency"],
                material=cleaned["material"],
                colour=cleaned["colour"],
                style=cleaned["style"],
                width=cleaned["width"],
                height=cleaned["height"],
                depth=cleaned["depth"],
                image_path=cleaned["image_path"],
                image_url=cleaned["image_url"],
                availability=cleaned["availability"],
                source=cleaned["source"],
            )
            valid_products_to_add.append(product_obj)

        if valid_products_to_add:
            self.session.add_all(valid_products_to_add)
            self.session.commit()
            report.valid_records_loaded = len(valid_products_to_add)
            logger.info(
                f"Successfully ingested {report.valid_records_loaded} new products into database"
            )
        else:
            logger.info("No new products to add (all existed or invalid)")

        report.finished_at = datetime.utcnow().isoformat()
        return report
