#!/usr/bin/env python3
"""
Comprehensive Test Script for Redesigned Extraction System
Tests multi-stage extraction with optimal graph structure using better OLLAMA models
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

from redesigned_methodology_extractor import (
    RedesignedOllamaExtractor,
    RedesignedPDFProcessor,
    RedesignedNeo4jIngester,
    RedesignedMethodologyProcessor
)

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Model options: mistral:7b (best for extraction), llama3.1:8b (good balance), codellama:7b (fastest)
TEST_MODELS = ["mistral:7b", "llama3.1:8b"]

class ComprehensiveTester:
    """Test the redesigned extraction system comprehensively"""
    
    def __init__(self, test_dir: Path, output_file: str = None):
        self.test_dir = test_dir
        self.output_file = output_file or f"redesigned_extraction_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.results = {
            "test_info": {
                "test_dir": str(test_dir),
                "test_timestamp": datetime.now().isoformat(),
                "models_tested": TEST_MODELS,
                "papers_tested": []
            },
            "results_by_model": {},
            "summary": {}
        }
    
    def test_model(self, model_name: str, pdf_files: List[Path]) -> Dict[str, Any]:
        """Test extraction with a specific model"""
        logger.info(f"\n{'='*70}")
        logger.info(f"Testing with model: {model_name}")
        logger.info(f"{'='*70}\n")
        
        extractor = RedesignedOllamaExtractor(model=model_name)
        pdf_processor = RedesignedPDFProcessor()
        
        model_results = {
            "model": model_name,
            "papers": [],
            "statistics": {
                "total_papers": len(pdf_files),
                "successful": 0,
                "failed": 0,
                "avg_methods_per_paper": 0,
                "avg_confidence": 0.0
            }
        }
        
        total_methods = 0
        total_confidence = 0.0
        successful_papers = 0
        
        for i, pdf_path in enumerate(pdf_files, 1):
            paper_id = pdf_path.stem
            logger.info(f"\n[{i}/{len(pdf_files)}] Processing: {paper_id}")
            
            try:
                # Extract text
                text = pdf_processor.extract_text_from_pdf(pdf_path)
                if not text:
                    logger.warning(f"  ⚠️ Failed to extract text from {pdf_path}")
                    model_results["papers"].append({
                        "paper_id": paper_id,
                        "status": "failed",
                        "error": "Failed to extract text"
                    })
                    continue
                
                # Stage 1: Identify methodology section
                logger.info("  Stage 1: Identifying methodology section...")
                section_info = extractor.identify_methodology_section(text)
                methodology_text = section_info.get("section_text", "")
                section_confidence = section_info.get("confidence", 0.0)
                
                if not methodology_text:
                    logger.warning(f"  ⚠️ No methodology section found, using first 10k chars")
                    methodology_text = text[:10000]
                    section_confidence = 0.3
                
                logger.info(f"  ✓ Section found: {len(methodology_text)} chars, confidence: {section_confidence:.2f}")
                
                # Stage 2: Extract primary methods
                logger.info("  Stage 2: Extracting primary methods...")
                primary_methods = extractor.extract_primary_methods(methodology_text, paper_id)
                method_type = primary_methods.get("method_type", "unknown")
                primary_method_list = primary_methods.get("primary_methods", [])
                primary_confidence = primary_methods.get("confidence", 0.0)
                
                logger.info(f"  ✓ Method type: {method_type}")
                logger.info(f"  ✓ Primary methods: {primary_method_list}")
                
                # Stage 3: Extract details for each method
                logger.info(f"  Stage 3: Extracting details for {len(primary_method_list)} methods...")
                methods_data = []
                for method_name in primary_method_list:
                    # Stage 4: Validate method
                    is_valid, validation_confidence = extractor.validate_method_in_text(method_name, methodology_text)
                    
                    if is_valid:
                        logger.info(f"    Validating '{method_name}'... ✓ (confidence: {validation_confidence:.2f})")
                        method_details = extractor.extract_method_details(method_name, methodology_text, method_type)
                        method_details["method_name"] = method_name
                        method_details["method_type"] = method_type
                        method_details["confidence"] = validation_confidence * method_details.get("confidence", 0.8)
                        methods_data.append(method_details)
                    else:
                        logger.warning(f"    Validating '{method_name}'... ✗ (not found in text)")
                
                # Calculate statistics
                if methods_data:
                    successful_papers += 1
                    total_methods += len(methods_data)
                    avg_method_confidence = sum(m.get("confidence", 0.0) for m in methods_data) / len(methods_data)
                    total_confidence += avg_method_confidence
                
                # Store results
                paper_result = {
                    "paper_id": paper_id,
                    "status": "success",
                    "section_detection": {
                        "found": section_info.get("section_found", False),
                        "confidence": section_confidence,
                        "text_length": len(methodology_text)
                    },
                    "primary_extraction": {
                        "method_type": method_type,
                        "primary_methods": primary_method_list,
                        "confidence": primary_confidence
                    },
                    "detailed_extraction": {
                        "methods_count": len(methods_data),
                        "methods": methods_data,
                        "avg_confidence": sum(m.get("confidence", 0.0) for m in methods_data) / len(methods_data) if methods_data else 0.0
                    }
                }
                
                model_results["papers"].append(paper_result)
                logger.info(f"  ✓ Successfully extracted {len(methods_data)} methods")
                
            except Exception as e:
                logger.error(f"  ✗ Error processing {paper_id}: {e}")
                model_results["papers"].append({
                    "paper_id": paper_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Calculate final statistics
        model_results["statistics"]["successful"] = successful_papers
        model_results["statistics"]["failed"] = len(pdf_files) - successful_papers
        if successful_papers > 0:
            model_results["statistics"]["avg_methods_per_paper"] = total_methods / successful_papers
            model_results["statistics"]["avg_confidence"] = total_confidence / successful_papers
        
        return model_results
    
    def run_tests(self, max_papers: int = 5):
        """Run comprehensive tests"""
        logger.info(f"\n{'='*70}")
        logger.info("COMPREHENSIVE REDESIGNED EXTRACTION SYSTEM TEST")
        logger.info(f"{'='*70}\n")
        
        # Find PDF files
        pdf_files = list(self.test_dir.glob("*.pdf"))[:max_papers]
        if not pdf_files:
            logger.error(f"No PDF files found in {self.test_dir}")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files to test")
        self.results["test_info"]["papers_tested"] = [f.stem for f in pdf_files]
        
        # Test each model
        for model_name in TEST_MODELS:
            try:
                model_results = self.test_model(model_name, pdf_files)
                self.results["results_by_model"][model_name] = model_results
            except Exception as e:
                logger.error(f"Failed to test model {model_name}: {e}")
                self.results["results_by_model"][model_name] = {
                    "model": model_name,
                    "error": str(e)
                }
        
        # Generate summary
        self._generate_summary()
        
        # Save results
        output_path = Path(self.output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Test complete! Results saved to: {output_path}")
        logger.info(f"{'='*70}\n")
        
        # Print summary
        self._print_summary()
    
    def _generate_summary(self):
        """Generate summary statistics"""
        summary = {
            "models_tested": len(self.results["results_by_model"]),
            "best_model": None,
            "model_comparison": {}
        }
        
        best_avg_confidence = 0.0
        for model_name, model_results in self.results["results_by_model"].items():
            if "error" in model_results:
                continue
            
            stats = model_results.get("statistics", {})
            model_summary = {
                "success_rate": stats.get("successful", 0) / stats.get("total_papers", 1),
                "avg_methods_per_paper": stats.get("avg_methods_per_paper", 0),
                "avg_confidence": stats.get("avg_confidence", 0.0)
            }
            
            summary["model_comparison"][model_name] = model_summary
            
            if model_summary["avg_confidence"] > best_avg_confidence:
                best_avg_confidence = model_summary["avg_confidence"]
                summary["best_model"] = model_name
        
        self.results["summary"] = summary
    
    def _print_summary(self):
        """Print summary to console"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        summary = self.results.get("summary", {})
        print(f"\nModels Tested: {summary.get('models_tested', 0)}")
        
        if summary.get("best_model"):
            print(f"Best Model: {summary['best_model']}")
        
        print("\nModel Comparison:")
        for model_name, comparison in summary.get("model_comparison", {}).items():
            print(f"\n  {model_name}:")
            print(f"    Success Rate: {comparison['success_rate']:.1%}")
            print(f"    Avg Methods/Paper: {comparison['avg_methods_per_paper']:.1f}")
            print(f"    Avg Confidence: {comparison['avg_confidence']:.2f}")
        
        print("\n" + "="*70)


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test redesigned extraction system")
    parser.add_argument("--dir", type=str, default="2025-2029", help="Directory with PDFs to test")
    parser.add_argument("--max-papers", type=int, default=5, help="Maximum number of papers to test")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file path")
    
    args = parser.parse_args()
    
    test_dir = Path(args.dir)
    if not test_dir.exists():
        logger.error(f"Directory not found: {test_dir}")
        return
    
    tester = ComprehensiveTester(test_dir, args.output)
    tester.run_tests(max_papers=args.max_papers)


if __name__ == "__main__":
    main()

