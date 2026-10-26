import argparse
from pathlib import Path

from app.config import settings
from app.core.database import SessionLocal, init_db
from app.services.ingestion import IngestionPipeline


def run_ingestion(file_path: Path, force: bool):
    print("Initializing database tables...")
    init_db()
    with SessionLocal() as session:
        pipeline = IngestionPipeline(session)
        print(f"Ingesting catalogue from: {file_path}")
        report = pipeline.ingest_file(file_path, force_reload=force)
        print("\n--- INGESTION SUMMARY ---")
        print(f"Total rows read:      {report.total_rows_read}")
        print(f"Valid rows inserted:  {report.valid_records_loaded}")
        print(f"Duplicates skipped:   {report.duplicates_skipped}")
        print(f"Invalid rows count:   {len(report.invalid_rows)}")
        if report.invalid_rows:
            print("Invalid rows sample:")
            for inv in report.invalid_rows[:3]:
                print(f"  - Row {inv['index']}: {inv['reason']}")
        print(f"Categories ingested:  {report.categories_found}")
        print("Ingestion complete.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest furniture catalogue into FurniFind AI")
    parser.add_argument(
        "--file",
        type=str,
        default=str(settings.SAMPLE_CATALOGUE_PATH),
        help="Path to catalogue JSON",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force reload and clear existing records"
    )
    args = parser.parse_args()

    run_ingestion(Path(args.file), args.force)
