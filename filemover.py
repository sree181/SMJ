
#instance SMJ
#username neo4j
#xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw

import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple


YEAR_REGEX = re.compile(r"(?<!\d)((19|20)\d{2})(?!\d)")


def extract_year_from_filename(filename: str) -> Optional[int]:
    """Return the first 4-digit year (1900-2099) found in the filename, or None."""
    match = YEAR_REGEX.search(filename)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def compute_five_year_bucket(year: int) -> Tuple[int, int]:
    """Return (start_year, end_year) for the 5-year bucket that contains the given year.

    Buckets are aligned to multiples of 5, inclusive, e.g. 1985-1989, 1990-1994, ...
    """
    start = (year // 5) * 5
    end = start + 4
    return start, end


def format_bucket_name(start_year: int, end_year: int) -> str:
    return f"{start_year}-{end_year}"


def find_pdf_files(base_dir: Path) -> List[Path]:
    """Return list of PDF files directly under base_dir (not recursive)."""
    return [p for p in base_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"]


def plan_moves(pdfs: List[Path]) -> Tuple[Dict[str, List[Path]], List[Path]]:
    """Plan which PDFs go to which bucket directory.

    Returns a tuple: (bucket_name -> list of PDFs, unknown_year_pdfs)
    """
    bucket_to_files: Dict[str, List[Path]] = {}
    unknown: List[Path] = []

    for pdf in pdfs:
        year = extract_year_from_filename(pdf.name)
        if year is None:
            unknown.append(pdf)
            continue

        start, end = compute_five_year_bucket(year)
        bucket = format_bucket_name(start, end)
        bucket_to_files.setdefault(bucket, []).append(pdf)

    return bucket_to_files, unknown


def ensure_directory(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def safe_move(src: Path, dst: Path) -> Path:
    """Move src to dst. If dst exists, append a numeric suffix to avoid collision."""
    if not dst.exists():
        shutil.move(str(src), str(dst))
        return dst

    stem = dst.stem
    suffix = dst.suffix
    parent = dst.parent
    index = 1
    while True:
        candidate = parent / f"{stem} ({index}){suffix}"
        if not candidate.exists():
            shutil.move(str(src), str(candidate))
            return candidate
        index += 1


def move_pdfs_to_buckets(base_dir: Path) -> None:
    pdfs = find_pdf_files(base_dir)
    bucket_to_files, unknown = plan_moves(pdfs)

    # Create bucket directories and move files
    moved_counts: Dict[str, int] = {}
    for bucket, files in sorted(bucket_to_files.items()):
        bucket_dir = base_dir / bucket
        ensure_directory(bucket_dir)
        count = 0
        for pdf in files:
            destination = bucket_dir / pdf.name
            safe_move(pdf, destination)
            count += 1
        moved_counts[bucket] = count

    # Handle unknown year files
    unknown_count = 0
    if unknown:
        unknown_dir = base_dir / "unknown_year"
        ensure_directory(unknown_dir)
        for pdf in unknown:
            destination = unknown_dir / pdf.name
            safe_move(pdf, destination)
            unknown_count += 1

    # Summary
    print("Move summary:")
    for bucket in sorted(moved_counts.keys()):
        print(f"  {bucket}: {moved_counts[bucket]} files")
    if unknown_count:
        print(f"  unknown_year: {unknown_count} files")
    print("Done.")


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    move_pdfs_to_buckets(base_dir)


if __name__ == "__main__":
    main()


