#!/usr/bin/env python3
"""
Test script for robust connection strength calculator
Demonstrates the mathematical model with various examples
"""

from connection_strength_calculator import ConnectionStrengthCalculator

def test_example_1():
    """Example 1: Primary theory + same section + keyword overlap"""
    print("\n" + "="*80)
    print("Example 1: Primary Theory + Same Section + Strong Keyword Overlap")
    print("="*80)
    
    theory = {
        "theory_name": "Resource-Based View",
        "role": "primary",
        "section": "introduction",
        "usage_context": "explains how firms allocate resources during financial crises"
    }
    
    phenomenon = {
        "phenomenon_name": "Resource allocation patterns during financial crises",
        "section": "introduction",
        "context": "Studied through firm investment decisions",
        "description": "How firms allocate resources during financial crises"
    }
    
    calculator = ConnectionStrengthCalculator(use_embeddings=False)
    strength, factors = calculator.calculate_strength(theory, phenomenon)
    
    print(f"\nTheory: {theory['theory_name']} ({theory['role']})")
    print(f"Phenomenon: {phenomenon['phenomenon_name']}")
    print(f"\nFactor Scores:")
    print(f"  Role Weight:        {factors['role_weight']:.3f} (theory is primary)")
    print(f"  Section Score:      {factors['section_score']:.3f} (same section)")
    print(f"  Keyword Score:      {factors['keyword_score']:.3f} (Jaccard similarity)")
    print(f"  Semantic Score:     {factors['semantic_score']:.3f} (n-gram overlap)")
    print(f"  Explicit Bonus:     {factors['explicit_bonus']:.3f} (key words match)")
    print(f"\n{'─'*80}")
    print(f"  TOTAL STRENGTH:     {strength:.3f}")
    print(f"{'─'*80}")
    print(f"Interpretation: {'Very Strong' if strength >= 0.8 else 'Strong' if strength >= 0.6 else 'Moderate' if strength >= 0.4 else 'Weak'}")
    
    return strength, factors

def test_example_2():
    """Example 2: Supporting theory + different section + moderate overlap"""
    print("\n" + "="*80)
    print("Example 2: Supporting Theory + Different Section + Moderate Overlap")
    print("="*80)
    
    theory = {
        "theory_name": "Agency Theory",
        "role": "supporting",
        "section": "literature_review",
        "usage_context": "discusses principal-agent relationships in corporate governance"
    }
    
    phenomenon = {
        "phenomenon_name": "Corporate governance structures",
        "section": "introduction",
        "context": "Examined through board composition",
        "description": "Corporate governance structures and their impact on firm performance"
    }
    
    calculator = ConnectionStrengthCalculator(use_embeddings=False)
    strength, factors = calculator.calculate_strength(theory, phenomenon)
    
    print(f"\nTheory: {theory['theory_name']} ({theory['role']})")
    print(f"Phenomenon: {phenomenon['phenomenon_name']}")
    print(f"\nFactor Scores:")
    print(f"  Role Weight:        {factors['role_weight']:.3f} (theory is supporting)")
    print(f"  Section Score:      {factors['section_score']:.3f} (adjacent sections)")
    print(f"  Keyword Score:      {factors['keyword_score']:.3f} (Jaccard similarity)")
    print(f"  Semantic Score:     {factors['semantic_score']:.3f} (n-gram overlap)")
    print(f"  Explicit Bonus:     {factors['explicit_bonus']:.3f} (key words match)")
    print(f"\n{'─'*80}")
    print(f"  TOTAL STRENGTH:     {strength:.3f}")
    print(f"{'─'*80}")
    print(f"Interpretation: {'Very Strong' if strength >= 0.8 else 'Strong' if strength >= 0.6 else 'Moderate' if strength >= 0.4 else 'Weak'}")
    
    return strength, factors

def test_example_3():
    """Example 3: Primary theory + explicit mention"""
    print("\n" + "="*80)
    print("Example 3: Primary Theory + Explicit Phenomenon Mention")
    print("="*80)
    
    theory = {
        "theory_name": "Institutional Theory",
        "role": "primary",
        "section": "introduction",
        "usage_context": "explains economic nationalism in court rulings and regulatory decisions"
    }
    
    phenomenon = {
        "phenomenon_name": "Economic nationalism in court rulings",
        "section": "introduction",
        "context": "Examined through judicial decisions",
        "description": "Economic nationalism in court rulings and regulatory decisions"
    }
    
    calculator = ConnectionStrengthCalculator(use_embeddings=False)
    strength, factors = calculator.calculate_strength(theory, phenomenon)
    
    print(f"\nTheory: {theory['theory_name']} ({theory['role']})")
    print(f"Phenomenon: {phenomenon['phenomenon_name']}")
    print(f"\nFactor Scores:")
    print(f"  Role Weight:        {factors['role_weight']:.3f} (theory is primary)")
    print(f"  Section Score:      {factors['section_score']:.3f} (same section)")
    print(f"  Keyword Score:      {factors['keyword_score']:.3f} (Jaccard similarity)")
    print(f"  Semantic Score:     {factors['semantic_score']:.3f} (n-gram overlap)")
    print(f"  Explicit Bonus:     {factors['explicit_bonus']:.3f} (EXACT MATCH!)")
    print(f"\n{'─'*80}")
    print(f"  TOTAL STRENGTH:     {strength:.3f}")
    print(f"{'─'*80}")
    print(f"Interpretation: {'Very Strong' if strength >= 0.8 else 'Strong' if strength >= 0.6 else 'Moderate' if strength >= 0.4 else 'Weak'}")
    
    return strength, factors

def test_example_4():
    """Example 4: Weak connection (challenging theory + no overlap)"""
    print("\n" + "="*80)
    print("Example 4: Challenging Theory + Weak Overlap (Should be below threshold)")
    print("="*80)
    
    theory = {
        "theory_name": "Transaction Cost Economics",
        "role": "challenging",
        "section": "discussion",
        "usage_context": "critiques market-based explanations"
    }
    
    phenomenon = {
        "phenomenon_name": "Firm innovation patterns",
        "section": "introduction",
        "context": "Studied through patent applications",
        "description": "How firms innovate and develop new products"
    }
    
    calculator = ConnectionStrengthCalculator(use_embeddings=False)
    strength, factors = calculator.calculate_strength(theory, phenomenon)
    
    print(f"\nTheory: {theory['theory_name']} ({theory['role']})")
    print(f"Phenomenon: {phenomenon['phenomenon_name']}")
    print(f"\nFactor Scores:")
    print(f"  Role Weight:        {factors['role_weight']:.3f} (theory is challenging)")
    print(f"  Section Score:      {factors['section_score']:.3f} (distant sections)")
    print(f"  Keyword Score:      {factors['keyword_score']:.3f} (no overlap)")
    print(f"  Semantic Score:     {factors['semantic_score']:.3f} (no overlap)")
    print(f"  Explicit Bonus:     {factors['explicit_bonus']:.3f} (no mention)")
    print(f"\n{'─'*80}")
    print(f"  TOTAL STRENGTH:     {strength:.3f}")
    print(f"{'─'*80}")
    print(f"Interpretation: {'Very Strong' if strength >= 0.8 else 'Strong' if strength >= 0.6 else 'Moderate' if strength >= 0.4 else 'Weak'}")
    print(f"Should create connection? {calculator.should_create_connection(strength, threshold=0.3)}")
    
    return strength, factors

def test_comparison():
    """Compare old vs new approach"""
    print("\n" + "="*80)
    print("Comparison: Old Binary Model vs New Mathematical Model")
    print("="*80)
    
    examples = [
        {
            "name": "Primary + Same Section",
            "theory": {"role": "primary", "section": "introduction", "usage_context": "explains resource allocation"},
            "phenomenon": {"section": "introduction", "context": "resource allocation patterns", "description": "resource allocation"}
        },
        {
            "name": "Primary + Different Section",
            "theory": {"role": "primary", "section": "literature_review", "usage_context": "explains resource allocation"},
            "phenomenon": {"section": "introduction", "context": "resource allocation patterns", "description": "resource allocation"}
        },
        {
            "name": "Supporting + Same Section",
            "theory": {"role": "supporting", "section": "introduction", "usage_context": "discusses resource allocation"},
            "phenomenon": {"section": "introduction", "context": "resource allocation patterns", "description": "resource allocation"}
        },
        {
            "name": "Supporting + Different Section",
            "theory": {"role": "supporting", "section": "literature_review", "usage_context": "discusses resource allocation"},
            "phenomenon": {"section": "introduction", "context": "resource allocation patterns", "description": "resource allocation"}
        }
    ]
    
    calculator = ConnectionStrengthCalculator(use_embeddings=False)
    
    print(f"\n{'Scenario':<30} {'Old Model':<15} {'New Model':<15} {'Improvement':<15}")
    print("─" * 75)
    
    for example in examples:
        theory = example["theory"]
        phenomenon = example["phenomenon"]
        
        # Old model
        old_strength = 0.7 if theory["role"] == "primary" else 0.5
        
        # New model
        strength, factors = calculator.calculate_strength(theory, phenomenon)
        
        improvement = "More nuanced" if abs(strength - old_strength) > 0.1 else "Similar"
        
        print(f"{example['name']:<30} {old_strength:<15.3f} {strength:<15.3f} {improvement:<15}")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("ROBUST CONNECTION STRENGTH CALCULATOR - TEST SUITE")
    print("="*80)
    
    # Run all tests
    test_example_1()
    test_example_2()
    test_example_3()
    test_example_4()
    test_comparison()
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)
    print("\nKey Improvements:")
    print("  ✓ Multi-factor mathematical model (5 factors)")
    print("  ✓ Continuous scale (0.0-1.0) instead of binary (0.5/0.7)")
    print("  ✓ Jaccard similarity for keyword overlap")
    print("  ✓ Section distance calculation")
    print("  ✓ Explicit mention detection")
    print("  ✓ Optional embedding-based semantic similarity")
    print("  ✓ Transparent factor scores stored in relationships")
    print("  ✓ Configurable threshold (default: 0.3)")

