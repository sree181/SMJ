#!/usr/bin/env python3
"""
Analyze papers in the 2025-2025 bucket.

paper_id in Neo4j is the PDF filename stem (e.g. 2025_123.pdf -> paper_id "2025_123"),
so the year is in the filename. Many papers had year=0/NULL at ingest and were
backfilled to 2025; this script uses paper_id (filename) to recover the real year.

1. Lists all papers with year=2025 and infers year from paper_id (YYYY_*).
2. Reports how many are likely backfilled (different year in filename) vs no year in id.
3. Run fix_2025_bucket_from_paper_id.py to set p.year from paper_id.
"""

import os
import re
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


def year_from_paper_id(paper_id: str):
    """Extract 4-digit year from paper_id if it matches YYYY_* or similar."""
    if not paper_id:
        return None
    m = re.match(r"^(\d{4})[_\-]", str(paper_id))
    if m:
        y = int(m.group(1))
        if 1980 <= y <= 2030:
            return y
    return None


def main():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not all([uri, password]):
        print("❌ Set NEO4J_URI and NEO4J_PASSWORD")
        return

    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        # All papers with year = 2025 (the "2025-2025" bucket)
        result = session.run("""
            MATCH (p:Paper)
            WHERE p.year = 2025
            RETURN p.paper_id AS paper_id, p.title AS title
            ORDER BY p.paper_id
        """)
        rows = list(result.data())

    driver.close()

    total_2025 = len(rows)
    # Papers whose paper_id suggests a different year (likely backfilled)
    inferred_other_year = []
    no_year_in_id = []

    for r in rows:
        pid = r.get("paper_id") or ""
        inferred = year_from_paper_id(pid)
        if inferred is not None and inferred != 2025:
            inferred_other_year.append((pid, r.get("title", "")[:50], inferred))
        elif inferred is None:
            no_year_in_id.append((pid, r.get("title", "")[:50]))

    print("=" * 70)
    print("📊 2025-2025 BUCKET ANALYSIS")
    print("=" * 70)
    print()
    print("Note: paper_id in Neo4j = PDF filename without .pdf (e.g. 2019_456.pdf -> 2019_456).")
    print()
    print(f"Total papers in 2025-2025 bucket (year=2025): {total_2025}")
    print()
    print("These are NOT all real 2025 papers. Previously, 276 papers had")
    print("missing/invalid year and were set to 2025 as a placeholder.")
    print()
    print("Breakdown:")
    print(f"  • Papers with year=2025 whose paper_id implies a different year: {len(inferred_other_year)}")
    print(f"  • Papers with year=2025 and no YYYY_ in paper_id: {len(no_year_in_id)}")
    print()
    if inferred_other_year:
        # Count by inferred year
        by_year = {}
        for _, _, y in inferred_other_year:
            by_year[y] = by_year.get(y, 0) + 1
        print("Inferred year from paper_id (likely backfilled, not really 2025):")
        for y in sorted(by_year.keys()):
            print(f"  {y}: {by_year[y]} papers")
        print()
        print("Sample paper_ids that suggest a different year (first 15):")
        for pid, title, y in inferred_other_year[:15]:
            print(f"  {pid} -> year {y}  |  {title}...")
    print()
    print("Conclusion:")
    print(f"  At most {total_2025 - len(inferred_other_year)} papers might be 'real' 2025 (or unknown).")
    print(f"  At least {len(inferred_other_year)} papers in the 2025 bucket are from other years (backfilled).")
    print()
    print("To fix: run  fix_2025_bucket_from_paper_id.py  to set year from paper_id where applicable.")
    print("=" * 70)


if __name__ == "__main__":
    main()
