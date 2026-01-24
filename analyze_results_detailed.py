#!/usr/bin/env python3
"""
Detailed analysis of high-performance pipeline results
Analyzes extraction quality, normalization effectiveness, and performance metrics
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any
import statistics

def load_json_file(filepath: Path) -> Dict[str, Any]:
    """Load JSON file safely"""
    if not filepath.exists():
        return {}
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {}

def analyze_extraction_quality(progress_file: Path, stats_file: Path) -> Dict[str, Any]:
    """Analyze extraction quality metrics"""
    progress = load_json_file(progress_file)
    stats = load_json_file(stats_file)
    
    analysis = {
        "total_papers": stats.get("total_papers", 0),
        "processed": stats.get("processed", 0),
        "failed": stats.get("failed", 0),
        "success_rate": stats.get("success_rate", 0),
        "papers_per_hour": stats.get("papers_per_hour", 0),
        "extraction_metrics": {},
        "normalization_metrics": {},
        "entity_counts": {}
    }
    
    # Extraction timing
    analysis["extraction_metrics"] = {
        "avg_time": stats.get("avg_extraction_time", 0),
        "total_time": stats.get("total_extraction_time", 0),
        "papers_per_hour": stats.get("papers_per_hour", 0)
    }
    
    # Normalization effectiveness
    analysis["normalization_metrics"] = {
        "coverage": stats.get("normalization_coverage", 0),
        "hits": stats.get("normalization_hits", 0),
        "misses": stats.get("normalization_misses", 0),
        "embedding_normalizations": stats.get("embedding_normalizations", 0),
        "avg_normalization_time": stats.get("avg_normalization_time", 0)
    }
    
    # Entity extraction counts
    analysis["entity_counts"] = {
        "theories": stats.get("total_theories", 0),
        "phenomena": stats.get("total_phenomena", 0),
        "methods": stats.get("total_methods", 0),
        "variables": stats.get("total_variables", 0),
        "findings": stats.get("total_findings", 0)
    }
    
    # Calculate averages per paper
    processed = stats.get("processed", 1)  # Avoid division by zero
    analysis["entities_per_paper"] = {
        "theories": analysis["entity_counts"]["theories"] / processed,
        "phenomena": analysis["entity_counts"]["phenomena"] / processed,
        "methods": analysis["entity_counts"]["methods"] / processed,
        "variables": analysis["entity_counts"]["variables"] / processed,
        "findings": analysis["entity_counts"]["findings"] / processed
    }
    
    return analysis

def analyze_errors(log_file: Path) -> Dict[str, Any]:
    """Analyze errors from log file"""
    if not log_file.exists():
        return {"error": "Log file not found"}
    
    errors = []
    error_types = defaultdict(int)
    
    with open(log_file, 'r') as f:
        for line in f:
            if "ERROR" in line or "error" in line.lower():
                errors.append(line.strip())
                # Categorize errors
                if "quota" in line.lower() or "429" in line.lower():
                    error_types["quota_exceeded"] += 1
                elif "timeout" in line.lower():
                    error_types["timeout"] += 1
                elif "connection" in line.lower():
                    error_types["connection"] += 1
                elif "extract" in line.lower():
                    error_types["extraction"] += 1
                else:
                    error_types["other"] += 1
    
    return {
        "total_errors": len(errors),
        "error_types": dict(error_types),
        "sample_errors": errors[:10]
    }

def check_neo4j_ingestion(paper_ids: List[str]) -> Dict[str, Any]:
    """Verify what was actually ingested into Neo4j"""
    try:
        from neo4j import GraphDatabase
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, user, password]):
            return {"error": "Neo4j credentials not found"}
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # Overall counts
            paper_count = session.run("MATCH (p:Paper) RETURN count(p) as count").single()["count"]
            theory_count = session.run("MATCH (t:Theory) RETURN count(t) as count").single()["count"]
            method_count = session.run("MATCH (m:Method) RETURN count(m) as count").single()["count"]
            phenomenon_count = session.run("MATCH (ph:Phenomenon) RETURN count(ph) as count").single()["count"]
            
            # Check specific papers
            found_papers = []
            missing_papers = []
            for paper_id in paper_ids:
                result = session.run(
                    "MATCH (p:Paper {paper_id: $paper_id}) RETURN p.paper_id as id, p.title as title, p.year as year",
                    paper_id=paper_id
                ).single()
                if result:
                    found_papers.append({
                        "paper_id": paper_id,
                        "title": result.get("title", "")[:60],
                        "year": result.get("year")
                    })
                else:
                    missing_papers.append(paper_id)
            
            # Get entities for found papers
            entities_per_paper = {}
            for paper in found_papers[:5]:  # Check first 5
                paper_id = paper["paper_id"]
                theories = session.run("""
                    MATCH (p:Paper {paper_id: $paper_id})-[:USES_THEORY]->(t:Theory)
                    RETURN count(t) as count
                """, paper_id=paper_id).single()["count"]
                
                methods = session.run("""
                    MATCH (p:Paper {paper_id: $paper_id})-[:USES_METHOD]->(m:Method)
                    RETURN count(m) as count
                """, paper_id=paper_id).single()["count"]
                
                phenomena = session.run("""
                    MATCH (p:Paper {paper_id: $paper_id})-[:STUDIES]->(ph:Phenomenon)
                    RETURN count(ph) as count
                """, paper_id=paper_id).single()["count"]
                
                entities_per_paper[paper_id] = {
                    "theories": theories,
                    "methods": methods,
                    "phenomena": phenomena
                }
        
        driver.close()
        
        return {
            "total_papers": paper_count,
            "total_theories": theory_count,
            "total_methods": method_count,
            "total_phenomena": phenomenon_count,
            "found_papers": found_papers,
            "missing_papers": missing_papers,
            "entities_per_paper": entities_per_paper,
            "verification_rate": len(found_papers) / len(paper_ids) * 100 if paper_ids else 0
        }
    except Exception as e:
        return {"error": str(e)}

def main():
    print("=" * 80)
    print("DETAILED PIPELINE RESULTS ANALYSIS")
    print("=" * 80)
    print()
    
    # Load files
    progress_file = Path("high_performance_progress.json")
    stats_file = Path("high_performance_stats.json")
    log_file = Path("high_performance_pipeline.log")
    
    # 1. Extraction Quality Analysis
    print("📊 EXTRACTION QUALITY ANALYSIS")
    print("-" * 80)
    quality = analyze_extraction_quality(progress_file, stats_file)
    
    print(f"Total Papers: {quality['total_papers']}")
    print(f"✅ Processed: {quality['processed']}")
    print(f"❌ Failed: {quality['failed']}")
    print(f"📈 Success Rate: {quality['success_rate']:.1f}%")
    print(f"⚡ Processing Rate: {quality['papers_per_hour']:.1f} papers/hour")
    print()
    
    print("⏱️  Timing Metrics:")
    print(f"   Avg extraction time: {quality['extraction_metrics']['avg_time']:.1f}s")
    print(f"   Avg normalization time: {quality['normalization_metrics']['avg_normalization_time']:.3f}s")
    print()
    
    print("📦 Entity Extraction:")
    for entity_type, count in quality['entity_counts'].items():
        avg = quality['entities_per_paper'].get(entity_type, 0)
        print(f"   {entity_type.capitalize()}: {count} total ({avg:.1f} per paper)")
    print()
    
    print("🔍 Normalization Effectiveness:")
    print(f"   Coverage: {quality['normalization_metrics']['coverage']:.1f}%")
    print(f"   Hits: {quality['normalization_metrics']['hits']}")
    print(f"   Misses: {quality['normalization_metrics']['misses']}")
    print(f"   Embedding normalizations: {quality['normalization_metrics']['embedding_normalizations']}")
    print()
    
    # 2. Error Analysis
    print("=" * 80)
    print("❌ ERROR ANALYSIS")
    print("-" * 80)
    errors = analyze_errors(log_file)
    
    if "error" in errors:
        print(f"   {errors['error']}")
    else:
        print(f"Total Errors: {errors['total_errors']}")
        if errors['error_types']:
            print("Error Breakdown:")
            for error_type, count in errors['error_types'].items():
                print(f"   {error_type}: {count}")
        if errors['sample_errors']:
            print("\nSample Errors:")
            for err in errors['sample_errors'][:5]:
                print(f"   {err[:100]}...")
    print()
    
    # 3. Neo4j Verification
    print("=" * 80)
    print("🗄️  NEO4J INGESTION VERIFICATION")
    print("-" * 80)
    
    progress_data = load_json_file(progress_file)
    processed_papers = progress_data.get("processed_papers", [])
    
    if processed_papers:
        neo4j_data = check_neo4j_ingestion(processed_papers)
        
        if "error" in neo4j_data:
            print(f"   ❌ {neo4j_data['error']}")
        else:
            print(f"✅ Total papers in Neo4j: {neo4j_data['total_papers']}")
            print(f"📊 Theories: {neo4j_data['total_theories']}")
            print(f"📊 Methods: {neo4j_data['total_methods']}")
            print(f"📊 Phenomena: {neo4j_data['total_phenomena']}")
            print(f"📈 Verification Rate: {neo4j_data['verification_rate']:.1f}%")
            print()
            
            if neo4j_data['found_papers']:
                print("✅ Verified Papers in Neo4j:")
                for paper in neo4j_data['found_papers'][:5]:
                    entities = neo4j_data['entities_per_paper'].get(paper['paper_id'], {})
                    print(f"   {paper['paper_id']} ({paper.get('year', 'N/A')}): "
                          f"{entities.get('theories', 0)} theories, "
                          f"{entities.get('methods', 0)} methods, "
                          f"{entities.get('phenomena', 0)} phenomena")
            
            if neo4j_data['missing_papers']:
                print(f"\n⚠️  Missing Papers ({len(neo4j_data['missing_papers'])}):")
                for paper_id in neo4j_data['missing_papers'][:5]:
                    print(f"   - {paper_id}")
    else:
        print("   No processed papers to verify")
    print()
    
    # 4. Performance Comparison
    print("=" * 80)
    print("📈 PERFORMANCE COMPARISON")
    print("-" * 80)
    
    if quality['papers_per_hour'] > 0:
        print("Current Performance:")
        print(f"   Papers/hour: {quality['papers_per_hour']:.1f}")
        print(f"   Success rate: {quality['success_rate']:.1f}%")
        print(f"   Normalization coverage: {quality['normalization_metrics']['coverage']:.1f}%")
        print()
        print("Target Performance (from objectives):")
        print("   Papers/hour: 200+")
        print("   Success rate: >95%")
        print("   Normalization coverage: >98%")
        print()
        
        # Calculate progress
        papers_per_hour_progress = (quality['papers_per_hour'] / 200) * 100
        success_rate_progress = (quality['success_rate'] / 95) * 100
        coverage_progress = (quality['normalization_metrics']['coverage'] / 98) * 100
        
        print("Progress toward targets:")
        print(f"   Speed: {papers_per_hour_progress:.1f}% of target")
        print(f"   Success rate: {success_rate_progress:.1f}% of target")
        print(f"   Coverage: {coverage_progress:.1f}% of target")
    print()
    
    # 5. Recommendations
    print("=" * 80)
    print("💡 RECOMMENDATIONS")
    print("-" * 80)
    
    if quality['failed'] > 0:
        print(f"⚠️  {quality['failed']} papers failed - review errors above")
    
    if quality['normalization_metrics']['coverage'] < 90:
        print("⚠️  Normalization coverage below target - consider expanding dictionary")
    
    if quality['papers_per_hour'] < 50:
        print("⚠️  Processing speed below target - consider increasing workers or optimizing")
    
    if quality['success_rate'] < 90:
        print("⚠️  Success rate below target - investigate error patterns")
    
    if quality['processed'] > 0 and quality['failed'] == 0:
        print("✅ Excellent! All papers processed successfully")
        print("   Ready to scale to larger batches")
    
    print()
    print("=" * 80)
    print("Analysis complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
