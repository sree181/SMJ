#!/usr/bin/env python3
"""
Async Processing Pipeline for SMJ Literature Analysis
High-throughput extraction with 20+ concurrent workers
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import aiofiles
from collections import defaultdict
import traceback

from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase
import redis.asyncio as redis
from tqdm.asyncio import tqdm

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PaperTask:
    """Task representing a paper to process"""
    paper_id: str
    pdf_path: Path
    status: ProcessingStatus = ProcessingStatus.PENDING
    priority: int = 0  # Higher = more urgent
    attempt: int = 0
    max_attempts: int = 3
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker_id: Optional[str] = None


@dataclass
class PipelineStats:
    """Pipeline execution statistics"""
    total_papers: int = 0
    processed: int = 0
    failed: int = 0
    skipped: int = 0
    in_progress: int = 0

    # Extraction counts
    total_theories: int = 0
    total_phenomena: int = 0
    total_methods: int = 0
    total_variables: int = 0
    total_findings: int = 0
    total_authors: int = 0

    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_extraction_time: float = 0.0

    # Error tracking
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['start_time'] = self.start_time.isoformat() if self.start_time else None
        result['end_time'] = self.end_time.isoformat() if self.end_time else None
        result['papers_per_minute'] = self._calculate_rate()
        result['success_rate'] = self._calculate_success_rate()
        return result

    def _calculate_rate(self) -> float:
        if not self.start_time:
            return 0.0
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        return self.processed / elapsed if elapsed > 0 else 0.0

    def _calculate_success_rate(self) -> float:
        total = self.processed + self.failed
        return (self.processed / total * 100) if total > 0 else 0.0


class AsyncProcessingPipeline:
    """
    High-throughput async processing pipeline for SMJ papers

    Features:
    - 20+ concurrent workers
    - Redis-backed task queue (optional)
    - Progress persistence
    - Automatic retry on failure
    - Real-time statistics
    """

    def __init__(self,
                 max_workers: int = 20,
                 neo4j_uri: str = None,
                 neo4j_user: str = None,
                 neo4j_password: str = None,
                 redis_url: str = None,
                 progress_file: Path = None):
        """
        Initialize the async pipeline

        Args:
            max_workers: Maximum concurrent workers
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            redis_url: Redis URL for distributed queue (optional)
            progress_file: File to save/load progress
        """
        self.max_workers = max_workers
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        self.redis_url = redis_url
        self.progress_file = progress_file or Path("pipeline_progress.json")

        # Task management
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.tasks: Dict[str, PaperTask] = {}
        self.results: Dict[str, Dict[str, Any]] = {}

        # Statistics
        self.stats = PipelineStats()

        # Synchronization
        self.semaphore: asyncio.Semaphore = asyncio.Semaphore(max_workers)
        self.lock = asyncio.Lock()

        # Neo4j driver (async)
        self.neo4j_driver = None

        # Redis client (optional)
        self.redis_client = None

        # Extractor (lazy loaded)
        self._extractor = None

        logger.info(f"Initialized AsyncProcessingPipeline with {max_workers} workers")

    async def _get_extractor(self):
        """Lazy load the extractor"""
        if self._extractor is None:
            from enhanced_gpt4_extractor import EnhancedGPT4Extractor
            self._extractor = EnhancedGPT4Extractor()
        return self._extractor

    async def _init_neo4j(self):
        """Initialize async Neo4j driver"""
        if self.neo4j_driver is None and self.neo4j_uri:
            self.neo4j_driver = AsyncGraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            logger.info("Initialized Neo4j async driver")

    async def _init_redis(self):
        """Initialize Redis client for distributed queue"""
        if self.redis_client is None and self.redis_url:
            self.redis_client = await redis.from_url(self.redis_url)
            logger.info("Initialized Redis client")

    async def close(self):
        """Clean up resources"""
        if self.neo4j_driver:
            await self.neo4j_driver.close()
        if self.redis_client:
            await self.redis_client.close()

    def discover_papers(self, base_dir: Path, year_range: tuple = None) -> List[Path]:
        """
        Discover PDF papers in directory structure

        Args:
            base_dir: Base directory containing papers
            year_range: Optional (start_year, end_year) filter

        Returns:
            List of PDF paths
        """
        papers = []
        pdf_patterns = ["*.pdf", "**/*.pdf"]

        for pattern in pdf_patterns:
            for pdf_path in base_dir.glob(pattern):
                # Extract year from filename (format: YYYY_XXX.pdf)
                try:
                    year = int(pdf_path.stem.split('_')[0])
                    if year_range:
                        if year < year_range[0] or year > year_range[1]:
                            continue
                    papers.append(pdf_path)
                except (ValueError, IndexError):
                    # Can't parse year, include anyway
                    papers.append(pdf_path)

        # Sort by year
        papers.sort(key=lambda p: p.stem)
        return papers

    async def load_progress(self) -> Dict[str, Any]:
        """Load progress from file"""
        if not self.progress_file.exists():
            return {"processed": [], "failed": []}

        try:
            async with aiofiles.open(self.progress_file, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            logger.warning(f"Failed to load progress: {e}")
            return {"processed": [], "failed": []}

    async def save_progress(self):
        """Save progress to file"""
        progress = {
            "processed": [
                {"paper_id": task.paper_id, "status": task.status.value}
                for task in self.tasks.values()
                if task.status == ProcessingStatus.COMPLETED
            ],
            "failed": [
                {"paper_id": task.paper_id, "error": task.error}
                for task in self.tasks.values()
                if task.status == ProcessingStatus.FAILED
            ],
            "stats": self.stats.to_dict(),
            "last_updated": datetime.now().isoformat()
        }

        try:
            async with aiofiles.open(self.progress_file, 'w') as f:
                await f.write(json.dumps(progress, indent=2, default=str))
        except Exception as e:
            logger.warning(f"Failed to save progress: {e}")

    async def _worker(self, worker_id: str):
        """
        Worker coroutine that processes papers from the queue

        Args:
            worker_id: Unique worker identifier
        """
        logger.debug(f"Worker {worker_id} started")

        while True:
            try:
                # Get task from queue (blocks until available)
                try:
                    task: PaperTask = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    # Check if we should exit
                    if self.task_queue.empty():
                        break
                    continue

                if task is None:  # Poison pill
                    self.task_queue.task_done()
                    break

                async with self.semaphore:
                    await self._process_task(task, worker_id)

                self.task_queue.task_done()

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                traceback.print_exc()

        logger.debug(f"Worker {worker_id} finished")

    async def _process_task(self, task: PaperTask, worker_id: str):
        """Process a single paper task"""
        task.status = ProcessingStatus.IN_PROGRESS
        task.started_at = datetime.now()
        task.worker_id = worker_id
        task.attempt += 1

        async with self.lock:
            self.stats.in_progress += 1

        try:
            logger.info(f"[{worker_id}] Processing {task.paper_id} (attempt {task.attempt})")

            # Get extractor
            extractor = await self._get_extractor()

            # Extract
            result = await extractor.extract_paper_async(task.pdf_path)

            # Update task
            task.status = ProcessingStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result.to_dict()

            # Update statistics
            async with self.lock:
                self.stats.processed += 1
                self.stats.in_progress -= 1
                self.stats.total_theories += len(result.theories)
                self.stats.total_phenomena += len(result.phenomena)
                self.stats.total_methods += len(result.methods)
                self.stats.total_variables += len(result.variables)
                self.stats.total_findings += len(result.findings)
                self.stats.total_authors += len(result.authors)

                extraction_time = (task.completed_at - task.started_at).total_seconds()
                self.stats.total_extraction_time += extraction_time

            # Ingest to Neo4j
            if self.neo4j_driver:
                await self._ingest_to_neo4j(result.to_dict())

            # Store result
            self.results[task.paper_id] = result.to_dict()

            logger.info(f"[{worker_id}] Completed {task.paper_id}: "
                       f"{len(result.theories)} theories, {len(result.phenomena)} phenomena, "
                       f"{len(result.methods)} methods")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{worker_id}] Failed {task.paper_id}: {error_msg}")

            if task.attempt < task.max_attempts:
                # Retry
                task.status = ProcessingStatus.PENDING
                task.error = error_msg
                await self.task_queue.put(task)
                logger.info(f"[{worker_id}] Requeued {task.paper_id} for retry")
            else:
                task.status = ProcessingStatus.FAILED
                task.error = error_msg

                async with self.lock:
                    self.stats.failed += 1
                    self.stats.in_progress -= 1
                    self.stats.errors.append({
                        "paper_id": task.paper_id,
                        "error": error_msg,
                        "attempts": task.attempt
                    })

    async def _ingest_to_neo4j(self, data: Dict[str, Any]):
        """Ingest extraction result to Neo4j"""
        if not self.neo4j_driver:
            return

        paper_id = data.get("paper_id", "unknown")

        async with self.neo4j_driver.session() as session:
            try:
                # Create Paper node
                await session.run("""
                    MERGE (p:Paper {paper_id: $paper_id})
                    SET p.title = $title,
                        p.abstract = $abstract,
                        p.publication_year = $year,
                        p.doi = $doi,
                        p.paper_type = $paper_type,
                        p.updated_at = datetime()
                """, {
                    "paper_id": paper_id,
                    "title": data.get("metadata", {}).get("title", ""),
                    "abstract": data.get("metadata", {}).get("abstract", ""),
                    "year": data.get("metadata", {}).get("publication_year"),
                    "doi": data.get("metadata", {}).get("doi"),
                    "paper_type": data.get("metadata", {}).get("paper_type")
                })

                # Create Theory nodes and relationships
                for theory in data.get("theories", []):
                    await session.run("""
                        MERGE (t:Theory {name: $name})
                        SET t.domain = $domain
                        WITH t
                        MATCH (p:Paper {paper_id: $paper_id})
                        MERGE (p)-[r:USES_THEORY]->(t)
                        SET r.role = $role,
                            r.usage_context = $usage_context,
                            r.confidence = $confidence
                    """, {
                        "paper_id": paper_id,
                        "name": theory.get("theory_name", ""),
                        "domain": theory.get("domain", ""),
                        "role": theory.get("role", "supporting"),
                        "usage_context": theory.get("usage_context", ""),
                        "confidence": theory.get("confidence", 0.8)
                    })

                # Create Phenomenon nodes and relationships
                for phenomenon in data.get("phenomena", []):
                    await session.run("""
                        MERGE (ph:Phenomenon {name: $name})
                        SET ph.type = $type,
                            ph.domain = $domain,
                            ph.description = $description,
                            ph.level_of_analysis = $level
                        WITH ph
                        MATCH (p:Paper {paper_id: $paper_id})
                        MERGE (p)-[r:STUDIES_PHENOMENON]->(ph)
                        SET r.context = $context,
                            r.confidence = $confidence
                    """, {
                        "paper_id": paper_id,
                        "name": phenomenon.get("phenomenon_name", ""),
                        "type": phenomenon.get("phenomenon_type", ""),
                        "domain": phenomenon.get("domain", ""),
                        "description": phenomenon.get("description", ""),
                        "level": phenomenon.get("level_of_analysis", ""),
                        "context": phenomenon.get("context", ""),
                        "confidence": phenomenon.get("confidence", 0.8)
                    })

                # Create Method nodes and relationships
                for method in data.get("methods", []):
                    await session.run("""
                        MERGE (m:Method {name: $name})
                        SET m.type = $type,
                            m.category = $category
                        WITH m
                        MATCH (p:Paper {paper_id: $paper_id})
                        MERGE (p)-[r:USES_METHOD]->(m)
                        SET r.sample_size = $sample_size,
                            r.time_period = $time_period,
                            r.confidence = $confidence
                    """, {
                        "paper_id": paper_id,
                        "name": method.get("method_name", ""),
                        "type": method.get("method_type", ""),
                        "category": method.get("method_category", ""),
                        "sample_size": method.get("sample_size", ""),
                        "time_period": method.get("time_period", ""),
                        "confidence": method.get("confidence", 0.8)
                    })

                # Create Author nodes and relationships
                for author in data.get("authors", []):
                    await session.run("""
                        MERGE (a:Author {name: $name})
                        SET a.given_name = $given_name,
                            a.family_name = $family_name
                        WITH a
                        MATCH (p:Paper {paper_id: $paper_id})
                        MERGE (p)-[r:AUTHORED_BY]->(a)
                        SET r.position = $position,
                            r.corresponding = $corresponding
                    """, {
                        "paper_id": paper_id,
                        "name": author.get("full_name", ""),
                        "given_name": author.get("given_name", ""),
                        "family_name": author.get("family_name", ""),
                        "position": author.get("position", 1),
                        "corresponding": author.get("corresponding_author", False)
                    })

                # Create Theory-Phenomenon relationships
                for link in data.get("extraction_metadata", {}).get("theory_phenomenon_links", []):
                    await session.run("""
                        MATCH (t:Theory {name: $theory_name})
                        MATCH (ph:Phenomenon {name: $phenomenon_name})
                        MERGE (t)-[r:EXPLAINS]->(ph)
                        SET r.relationship_type = $rel_type,
                            r.mechanism = $mechanism,
                            r.evidence_strength = $evidence,
                            r.paper_id = $paper_id
                    """, {
                        "paper_id": paper_id,
                        "theory_name": link.get("theory_name", ""),
                        "phenomenon_name": link.get("phenomenon_name", ""),
                        "rel_type": link.get("relationship_type", "explains"),
                        "mechanism": link.get("mechanism", ""),
                        "evidence": link.get("evidence_strength", "moderate")
                    })

            except Exception as e:
                logger.error(f"Neo4j ingestion failed for {paper_id}: {e}")

    async def run(self,
                  base_dir: Path,
                  year_range: tuple = None,
                  resume: bool = True) -> PipelineStats:
        """
        Run the processing pipeline

        Args:
            base_dir: Directory containing PDF papers
            year_range: Optional (start_year, end_year) filter
            resume: Whether to resume from previous progress

        Returns:
            Pipeline statistics
        """
        self.stats = PipelineStats()
        self.stats.start_time = datetime.now()

        # Initialize connections
        await self._init_neo4j()
        await self._init_redis()

        # Discover papers
        papers = self.discover_papers(base_dir, year_range)
        logger.info(f"Discovered {len(papers)} papers")

        # Load previous progress
        progress = {}
        if resume:
            progress = await self.load_progress()
            processed_ids = {p["paper_id"] for p in progress.get("processed", [])}
            logger.info(f"Resuming: {len(processed_ids)} papers already processed")
        else:
            processed_ids = set()

        # Create tasks
        for pdf_path in papers:
            paper_id = pdf_path.stem
            if paper_id in processed_ids:
                self.stats.skipped += 1
                continue

            task = PaperTask(
                paper_id=paper_id,
                pdf_path=pdf_path,
                status=ProcessingStatus.PENDING
            )
            self.tasks[paper_id] = task
            await self.task_queue.put(task)

        self.stats.total_papers = len(papers)
        logger.info(f"Queued {self.task_queue.qsize()} papers for processing")

        # Start workers
        workers = []
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i:02d}"))
            workers.append(worker)

        # Progress monitoring
        progress_task = asyncio.create_task(self._monitor_progress())

        # Wait for queue to be processed
        await self.task_queue.join()

        # Send poison pills to stop workers
        for _ in workers:
            await self.task_queue.put(None)

        # Wait for workers to finish
        await asyncio.gather(*workers)

        # Stop progress monitor
        progress_task.cancel()
        try:
            await progress_task
        except asyncio.CancelledError:
            pass

        # Finalize
        self.stats.end_time = datetime.now()
        await self.save_progress()
        await self.close()

        # Print final statistics
        self._print_summary()

        return self.stats

    async def _monitor_progress(self):
        """Monitor and report progress periodically"""
        while True:
            await asyncio.sleep(30)  # Report every 30 seconds

            rate = self.stats._calculate_rate()
            logger.info(
                f"Progress: {self.stats.processed}/{self.stats.total_papers} papers "
                f"({self.stats._calculate_success_rate():.1f}% success rate, "
                f"{rate:.1f} papers/min)"
            )

            # Save progress periodically
            await self.save_progress()

    def _print_summary(self):
        """Print processing summary"""
        duration = (self.stats.end_time - self.stats.start_time).total_seconds()
        rate = self.stats.processed / (duration / 60) if duration > 0 else 0

        print("\n" + "=" * 70)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 70)
        print(f"Total Papers:       {self.stats.total_papers}")
        print(f"Processed:          {self.stats.processed}")
        print(f"Failed:             {self.stats.failed}")
        print(f"Skipped:            {self.stats.skipped}")
        print(f"Success Rate:       {self.stats._calculate_success_rate():.1f}%")
        print(f"Processing Rate:    {rate:.1f} papers/minute")
        print(f"Total Duration:     {duration / 60:.1f} minutes")
        print()
        print("EXTRACTION STATISTICS:")
        print(f"  Theories:         {self.stats.total_theories}")
        print(f"  Phenomena:        {self.stats.total_phenomena}")
        print(f"  Methods:          {self.stats.total_methods}")
        print(f"  Variables:        {self.stats.total_variables}")
        print(f"  Findings:         {self.stats.total_findings}")
        print(f"  Authors:          {self.stats.total_authors}")
        print("=" * 70)


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="SMJ Literature Processing Pipeline")
    parser.add_argument("--base-dir", type=Path, default=Path("Strategic Management Journal"),
                       help="Base directory containing papers")
    parser.add_argument("--start-year", type=int, default=1985,
                       help="Start year for processing")
    parser.add_argument("--end-year", type=int, default=2024,
                       help="End year for processing")
    parser.add_argument("--workers", type=int, default=20,
                       help="Number of concurrent workers")
    parser.add_argument("--no-resume", action="store_true",
                       help="Start fresh, don't resume from progress")

    args = parser.parse_args()

    pipeline = AsyncProcessingPipeline(
        max_workers=args.workers
    )

    year_range = (args.start_year, args.end_year)

    stats = await pipeline.run(
        base_dir=args.base_dir,
        year_range=year_range,
        resume=not args.no_resume
    )

    # Save final stats
    with open("pipeline_final_stats.json", "w") as f:
        json.dump(stats.to_dict(), f, indent=2, default=str)


if __name__ == "__main__":
    asyncio.run(main())
