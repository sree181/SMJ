#!/usr/bin/env python3
"""
Fix all papers with missing or placeholder year by assigning year from filename.

paper_id in Neo4j is the PDF filename stem (e.g. 2019_456.pdf -> paper_id "2019_456").
This script finds ALL papers with:
  - year IS NULL or year <= 0 (missing), OR
  - year = 2025 (placeholder from earlier backfill)
and sets p.year from the YYYY in paper_id (YYYY_*) so they go to the correct year bucket.
Papers with no parseable year in paper_id are set to 2025 (unknown).
"""

import os
import re
from collections import defaultdict
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# Year range we accept from paper_id (dashboard range + 2025)
MIN_YEAR = 1985
MAX_YEAR = 2025


def year_from_paper_id(paper_id: str):
    """Extract 4-digit year from paper_id if it matches YYYY_* or YYYY-*."""
    if not paper_id:
        return None
    m = re.match(r"^(\d{4})[_\-]", str(paper_id).strip())
    if m:
        y = int(m.group(1))
        if MIN_YEAR <= y <= MAX_YEAR:
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

    # All papers with missing or placeholder year (NULL, <=0, or 2025)
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NULL OR p.year <= 0 OR p.year = 2025
            RETURN p.paper_id AS paper_id, p.year AS current_year
        """)
        rows = list(result.data())

    # Build list: (paper_id, new_year). Use 2025 as fallback when no year in paper_id.
    to_fix = []
    no_year_in_id = []
    for r in rows:
        pid = r.get("paper_id")
        current = r.get("current_year")
        y = year_from_paper_id(pid)
        if y is not None:
            to_fix.append((pid, y))
        else:
            no_year_in_id.append((pid, current))

    total_missing_or_placeholder = len(rows)
    print("=" * 60)
    print("Fix year from filename (paper_id = PDF stem)")
    print("=" * 60)
    print(f"Papers with missing or placeholder year: {total_missing_or_placeholder}")
    print(f"  -> With YYYY_ in paper_id (will set to that year): {len(to_fix)}")
    print(f"  -> No year in paper_id (will set to 2025): {len(no_year_in_id)}")
    print()

    if not to_fix and not no_year_in_id:
        print("No papers to update.")
        driver.close()
        return

    # Count by target year for reporting
    by_year = defaultdict(int)
    for _, y in to_fix:
        by_year[y] += 1
    for _ in no_year_in_id:
        by_year[2025] += 1

    print("Target year buckets (after fix):")
    for y in sorted(by_year.keys()):
        print(f"  {y}: {by_year[y]} papers")
    print()

    # Apply updates
    with driver.session() as session:
        for paper_id, new_year in to_fix:
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                SET p.year = $year
            """, paper_id=paper_id, year=new_year)
        for paper_id, _ in no_year_in_id:
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                SET p.year = 2025
            """, paper_id=paper_id)

    driver.close()
    print(f"✅ Updated {len(to_fix) + len(no_year_in_id)} papers into their respective year buckets.")
    print("   Re-run dashboard/analytics to see corrected intervals.")


if __name__ == "__main__":
    main()
