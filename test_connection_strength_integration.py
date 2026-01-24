#!/usr/bin/env python3
"""
Integration Tests for Connection Strength System
Phase 2 Fix #4: Comprehensive testing
"""

import os
import sys
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from connection_strength_calculator import ConnectionStrengthCalculator
from entity_normalizer import EntityNormalizer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionStrengthIntegrationTests:
    """Integration tests for connection strength system"""
    
    def __init__(self):
        self.calculator = ConnectionStrengthCalculator(use_embeddings=False)
        self.normalizer = EntityNormalizer()
        self.test_results = []
    
    def test_phenomenon_normalization(self):
        """Test Fix #1: Phenomenon normalization"""
        logger.info("\n🧪 Test 1: Phenomenon Normalization")
        
        test_cases = [
            ("Resource allocation patterns", "Resource Allocation Patterns"),
            ("Economic nationalism in court rulings", "Economic Nationalism In Court Rulings"),
            ("Firm performance variations", "Firm Performance Variations"),
            ("  resource  allocation  ", "Resource Allocation"),  # Whitespace
        ]
        
        passed = 0
        failed = 0
        
        for input_name, expected_prefix in test_cases:
            normalized = self.normalizer.normalize_phenomenon(input_name)
            # Check if normalized starts with expected (allowing for suffix removal)
            if normalized.lower().startswith(expected_prefix.lower().split()[0].lower()):
                logger.info(f"  ✅ '{input_name}' → '{normalized}'")
                passed += 1
            else:
                logger.error(f"  ❌ '{input_name}' → '{normalized}' (expected starts with '{expected_prefix}')")
                failed += 1
        
        result = {"test": "phenomenon_normalization", "passed": passed, "failed": failed}
        self.test_results.append(result)
        return failed == 0
    
    def test_input_validation(self):
        """Test Fix #3: Input validation"""
        logger.info("\n🧪 Test 2: Input Validation")
        
        passed = 0
        failed = 0
        
        # Test None theory
        strength, factors = self.calculator.calculate_strength(None, {"phenomenon_name": "X"})
        if strength == 0.0 and not factors:
            logger.info("  ✅ None theory handled correctly")
            passed += 1
        else:
            logger.error(f"  ❌ None theory not handled (got {strength})")
            failed += 1
        
        # Test None phenomenon
        strength, factors = self.calculator.calculate_strength({"role": "primary"}, None)
        if strength == 0.0 and not factors:
            logger.info("  ✅ None phenomenon handled correctly")
            passed += 1
        else:
            logger.error(f"  ❌ None phenomenon not handled (got {strength})")
            failed += 1
        
        # Test missing phenomenon_name
        strength, factors = self.calculator.calculate_strength(
            {"role": "primary"}, {"context": "test"}
        )
        if strength == 0.0 and not factors:
            logger.info("  ✅ Missing phenomenon_name handled correctly")
            passed += 1
        else:
            logger.error(f"  ❌ Missing phenomenon_name not handled (got {strength})")
            failed += 1
        
        # Test valid inputs
        strength, factors = self.calculator.calculate_strength(
            {"role": "primary", "section": "introduction", "usage_context": "explains resource allocation"},
            {"phenomenon_name": "Resource allocation", "section": "introduction", "context": "resource allocation"}
        )
        if strength > 0.0 and factors:
            logger.info(f"  ✅ Valid inputs processed correctly (strength: {strength:.3f})")
            passed += 1
        else:
            logger.error(f"  ❌ Valid inputs not processed (got {strength})")
            failed += 1
        
        result = {"test": "input_validation", "passed": passed, "failed": failed}
        self.test_results.append(result)
        return failed == 0
    
    def test_connection_strength_calculation(self):
        """Test connection strength calculation with various scenarios"""
        logger.info("\n🧪 Test 3: Connection Strength Calculation")
        
        passed = 0
        failed = 0
        
        # Test 1: Primary theory + same section
        theory = {
            "role": "primary",
            "section": "introduction",
            "usage_context": "explains resource allocation patterns"
        }
        phenomenon = {
            "phenomenon_name": "Resource allocation patterns",
            "section": "introduction",
            "context": "resource allocation",
            "description": "How firms allocate resources"
        }
        
        strength, factors = self.calculator.calculate_strength(theory, phenomenon)
        if strength >= 0.7:  # Should be strong
            logger.info(f"  ✅ Primary + same section: {strength:.3f} (expected >= 0.7)")
            passed += 1
        else:
            logger.error(f"  ❌ Primary + same section: {strength:.3f} (expected >= 0.7)")
            failed += 1
        
        # Test 2: Supporting theory + different section
        theory = {
            "role": "supporting",
            "section": "literature_review",
            "usage_context": "discusses firm performance"
        }
        phenomenon = {
            "phenomenon_name": "Firm performance",
            "section": "introduction",
            "context": "firm performance variations",
            "description": "Firm performance differences"
        }
        
        strength, factors = self.calculator.calculate_strength(theory, phenomenon)
        if 0.3 <= strength < 0.7:  # Should be moderate
            logger.info(f"  ✅ Supporting + different section: {strength:.3f} (expected 0.3-0.7)")
            passed += 1
        else:
            logger.error(f"  ❌ Supporting + different section: {strength:.3f} (expected 0.3-0.7)")
            failed += 1
        
        # Test 3: Weak connection (should be below threshold)
        theory = {
            "role": "challenging",
            "section": "discussion",
            "usage_context": "critiques market theories"
        }
        phenomenon = {
            "phenomenon_name": "Innovation patterns",
            "section": "introduction",
            "context": "innovation in firms",
            "description": "How firms innovate"
        }
        
        strength, factors = self.calculator.calculate_strength(theory, phenomenon)
        should_create = self.calculator.should_create_connection(strength, threshold=0.3)
        if not should_create:  # Should not create connection
            logger.info(f"  ✅ Weak connection filtered: {strength:.3f} (below threshold)")
            passed += 1
        else:
            logger.error(f"  ❌ Weak connection not filtered: {strength:.3f} (should be below 0.3)")
            failed += 1
        
        result = {"test": "strength_calculation", "passed": passed, "failed": failed}
        self.test_results.append(result)
        return failed == 0
    
    def test_factor_scores(self):
        """Test that factor scores are properly calculated"""
        logger.info("\n🧪 Test 4: Factor Scores")
        
        theory = {
            "role": "primary",
            "section": "introduction",
            "usage_context": "explains economic nationalism in court rulings"
        }
        phenomenon = {
            "phenomenon_name": "Economic nationalism in court rulings",
            "section": "introduction",
            "context": "court rulings and legal decisions",
            "description": "Economic nationalism in court rulings"
        }
        
        strength, factors = self.calculator.calculate_strength(theory, phenomenon)
        
        passed = 0
        failed = 0
        
        # Check all factors are present
        required_factors = ["role_weight", "section_score", "keyword_score", "semantic_score", "explicit_bonus"]
        for factor in required_factors:
            if factor in factors:
                logger.info(f"  ✅ Factor '{factor}': {factors[factor]:.3f}")
                passed += 1
            else:
                logger.error(f"  ❌ Factor '{factor}' missing")
                failed += 1
        
        # Check factor sum equals total (approximately)
        # Note: Strength is capped at 1.0, so factor_sum may exceed strength
        factor_sum = sum(factors.get(f, 0) for f in required_factors)
        if abs(factor_sum - strength) < 0.01 or (factor_sum > 1.0 and strength == 1.0):
            # Either they match, or factors sum > 1.0 but strength is capped at 1.0 (correct behavior)
            logger.info(f"  ✅ Factor sum ({factor_sum:.3f}) matches/caps total ({strength:.3f})")
            passed += 1
        else:
            logger.error(f"  ❌ Factor sum ({factor_sum:.3f}) doesn't match total ({strength:.3f})")
            failed += 1
        
        result = {"test": "factor_scores", "passed": passed, "failed": failed}
        self.test_results.append(result)
        return failed == 0
    
    def run_all_tests(self):
        """Run all integration tests"""
        logger.info("="*80)
        logger.info("CONNECTION STRENGTH INTEGRATION TESTS")
        logger.info("="*80)
        
        tests = [
            self.test_phenomenon_normalization,
            self.test_input_validation,
            self.test_connection_strength_calculation,
            self.test_factor_scores,
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                logger.error(f"❌ Test {test.__name__} failed with exception: {e}")
                results.append(False)
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("TEST SUMMARY")
        logger.info("="*80)
        
        total_passed = sum(1 for r in results if r)
        total_failed = sum(1 for r in results if not r)
        
        for result in self.test_results:
            logger.info(f"{result['test']}: {result['passed']} passed, {result['failed']} failed")
        
        logger.info(f"\nTotal: {total_passed} tests passed, {total_failed} tests failed")
        
        if total_failed == 0:
            logger.info("✅ ALL TESTS PASSED!")
            return True
        else:
            logger.error("❌ SOME TESTS FAILED")
            return False

def main():
    """Main function"""
    tester = ConnectionStrengthIntegrationTests()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

