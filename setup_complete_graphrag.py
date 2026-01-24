#!/usr/bin/env python3
"""
Complete Graph RAG Setup Script
Orchestrates: Embedding generation → Vector index creation → System verification
"""

import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main execution flow"""
    logger.info("=" * 80)
    logger.info("COMPLETE GRAPH RAG SETUP")
    logger.info("=" * 80)
    
    # Step 1: Generate embeddings
    logger.info("\n" + "=" * 80)
    logger.info("STEP 1: GENERATING EMBEDDINGS FOR ALL ENTITIES")
    logger.info("=" * 80)
    
    try:
        from generate_all_embeddings import EmbeddingGenerator
        generator = EmbeddingGenerator()
        try:
            generator.generate_all_embeddings()
            logger.info("✓ Embedding generation complete")
        finally:
            generator.close()
    except Exception as e:
        logger.error(f"✗ Error generating embeddings: {e}")
        logger.error("Please check your Neo4j connection and try again")
        sys.exit(1)
    
    # Step 2: Setup vector indexes and verify
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: SETTING UP VECTOR INDEXES")
    logger.info("=" * 80)
    
    try:
        from setup_graphrag_system import GraphRAGSetup
        setup = GraphRAGSetup()
        try:
            setup.setup_complete()
            logger.info("✓ Vector index setup complete")
        finally:
            setup.close()
    except Exception as e:
        logger.error(f"✗ Error setting up vector indexes: {e}")
        logger.warning("Vector indexes may not be supported, but embeddings are stored")
    
    # Step 3: Test Graph RAG query system
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: TESTING GRAPH RAG QUERY SYSTEM")
    logger.info("=" * 80)
    
    try:
        from graphrag_query_system import GraphRAGQuerySystem
        system = GraphRAGQuerySystem()
        try:
            test_query = "What theories explain competitive advantage?"
            logger.info(f"Test query: '{test_query}'")
            result = system.query(test_query, top_k=5)
            
            logger.info(f"✓ Query system working")
            logger.info(f"  - Papers found: {len(result.get('papers', []))}")
            logger.info(f"  - Theories found: {len(result.get('theories', []))}")
            logger.info(f"  - Phenomena found: {len(result.get('phenomena', []))}")
            logger.info(f"  - Total context papers: {result.get('total_papers', 0)}")
        finally:
            system.close()
    except Exception as e:
        logger.error(f"✗ Error testing query system: {e}")
        logger.warning("Query system may need embeddings to be generated first")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("SETUP COMPLETE")
    logger.info("=" * 80)
    logger.info("\nNext steps:")
    logger.info("1. Integrate GraphRAGQuerySystem with /api/query endpoint")
    logger.info("2. Test with comprehensive questions")
    logger.info("3. Monitor performance and adjust similarity thresholds")
    logger.info("\nTo use Graph RAG in your API:")
    logger.info("  from graphrag_query_system import GraphRAGQuerySystem")
    logger.info("  system = GraphRAGQuerySystem()")
    logger.info("  result = system.query('your question')")
    logger.info("  answer = system.generate_answer(result)")

if __name__ == "__main__":
    main()
