#!/usr/bin/env python3
"""
Quality Monitoring System
Real-time quality tracking and alerting for extraction pipeline
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from pathlib import Path

logger = logging.getLogger(__name__)

class QualityMonitor:
    """Real-time quality monitoring for extraction pipeline"""
    
    def __init__(self, metrics_file: Optional[Path] = None):
        self.metrics_file = metrics_file or Path("quality_metrics.json")
        
        # Real-time metrics
        self.metrics = {
            'extraction_success_rate': 0.0,
            'average_confidence': 0.0,
            'validation_failure_rate': 0.0,
            'entity_completeness': defaultdict(float),
            'extraction_times': deque(maxlen=100),  # Last 100 extractions
            'error_counts': defaultdict(int),
            'total_papers_processed': 0,
            'papers_with_issues': 0,
            'start_time': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat()
        }
        
        # Thresholds for alerting
        self.thresholds = {
            'extraction_success_rate': 0.80,  # Alert if below 80%
            'average_confidence': 0.75,  # Alert if below 75%
            'validation_failure_rate': 0.10,  # Alert if above 10%
            'entity_completeness_min': 0.70  # Alert if any entity type below 70%
        }
        
        # Alerts
        self.alerts = []
        
        # Load existing metrics if available
        self.load_metrics()
    
    def load_metrics(self):
        """Load metrics from file"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    saved_metrics = json.load(f)
                    # Merge with current metrics
                    for key, value in saved_metrics.items():
                        if key in self.metrics:
                            if isinstance(value, (int, float)):
                                self.metrics[key] = value
                            elif isinstance(value, dict):
                                self.metrics[key].update(value)
            except Exception as e:
                logger.warning(f"Error loading metrics: {e}")
    
    def save_metrics(self):
        """Save metrics to file"""
        try:
            self.metrics['last_update'] = datetime.now().isoformat()
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def track_extraction(self, paper_id: str, extraction_result: Dict[str, Any], 
                        extraction_time: float, source_text: str = None):
        """Track extraction quality for a single paper"""
        self.metrics['total_papers_processed'] += 1
        
        # Track extraction time
        self.metrics['extraction_times'].append(extraction_time)
        
        # Calculate success (has at least some entities)
        has_entities = (
            extraction_result.get('methods') or
            extraction_result.get('theories') or
            extraction_result.get('research_questions') or
            extraction_result.get('variables')
        )
        
        if not has_entities:
            self.metrics['papers_with_issues'] += 1
            self.metrics['error_counts']['no_entities'] += 1
        
        # Track entity completeness
        entity_counts = {
            'methods': len(extraction_result.get('methods', [])),
            'theories': len(extraction_result.get('theories', [])),
            'research_questions': len(extraction_result.get('research_questions', [])),
            'variables': len(extraction_result.get('variables', [])),
            'findings': len(extraction_result.get('findings', [])),
            'contributions': len(extraction_result.get('contributions', []))
        }
        
        # Update completeness (rolling average)
        for entity_type, count in entity_counts.items():
            current_avg = self.metrics['entity_completeness'][entity_type]
            n = self.metrics['total_papers_processed']
            # Update rolling average
            self.metrics['entity_completeness'][entity_type] = (
                (current_avg * (n - 1) + (1.0 if count > 0 else 0.0)) / n
            )
        
        # Calculate average confidence
        confidences = []
        for entity_list in [
            extraction_result.get('methods', []),
            extraction_result.get('theories', []),
            extraction_result.get('variables', [])
        ]:
            for entity in entity_list:
                if isinstance(entity, dict) and 'confidence' in entity:
                    confidences.append(float(entity['confidence']))
        
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            # Update rolling average
            current_avg_conf = self.metrics['average_confidence']
            n = self.metrics['total_papers_processed']
            self.metrics['average_confidence'] = (
                (current_avg_conf * (n - 1) + avg_conf) / n
            )
        
        # Update success rate
        success = 1.0 if has_entities else 0.0
        current_success_rate = self.metrics['extraction_success_rate']
        n = self.metrics['total_papers_processed']
        self.metrics['extraction_success_rate'] = (
            (current_success_rate * (n - 1) + success) / n
        )
        
        # Check thresholds and generate alerts
        self._check_thresholds(paper_id)
        
        # Save metrics periodically
        if self.metrics['total_papers_processed'] % 10 == 0:
            self.save_metrics()
    
    def track_validation(self, paper_id: str, validation_result: Dict[str, Any]):
        """Track validation results"""
        if not validation_result.get('valid', True):
            self.metrics['validation_failure_rate'] = (
                (self.metrics['validation_failure_rate'] * 
                 (self.metrics['total_papers_processed'] - 1) + 1.0) /
                self.metrics['total_papers_processed']
            )
            self.metrics['error_counts']['validation_failed'] += 1
        else:
            self.metrics['validation_failure_rate'] = (
                (self.metrics['validation_failure_rate'] * 
                 (self.metrics['total_papers_processed'] - 1) + 0.0) /
                self.metrics['total_papers_processed']
            )
    
    def track_error(self, paper_id: str, error_type: str, error_message: str):
        """Track errors"""
        self.metrics['error_counts'][error_type] += 1
        logger.error(f"Error for {paper_id}: {error_type} - {error_message}")
    
    def _check_thresholds(self, paper_id: str):
        """Check metrics against thresholds and generate alerts"""
        alerts = []
        
        # Check extraction success rate
        if self.metrics['extraction_success_rate'] < self.thresholds['extraction_success_rate']:
            alerts.append({
                'type': 'low_success_rate',
                'severity': 'high',
                'message': f"Extraction success rate ({self.metrics['extraction_success_rate']:.2%}) below threshold ({self.thresholds['extraction_success_rate']:.2%})",
                'paper_id': paper_id,
                'timestamp': datetime.now().isoformat()
            })
        
        # Check average confidence
        if self.metrics['average_confidence'] < self.thresholds['average_confidence']:
            alerts.append({
                'type': 'low_confidence',
                'severity': 'medium',
                'message': f"Average confidence ({self.metrics['average_confidence']:.2f}) below threshold ({self.thresholds['average_confidence']:.2f})",
                'paper_id': paper_id,
                'timestamp': datetime.now().isoformat()
            })
        
        # Check validation failure rate
        if self.metrics['validation_failure_rate'] > self.thresholds['validation_failure_rate']:
            alerts.append({
                'type': 'high_validation_failure',
                'severity': 'high',
                'message': f"Validation failure rate ({self.metrics['validation_failure_rate']:.2%}) above threshold ({self.thresholds['validation_failure_rate']:.2%})",
                'paper_id': paper_id,
                'timestamp': datetime.now().isoformat()
            })
        
        # Check entity completeness
        for entity_type, completeness in self.metrics['entity_completeness'].items():
            if completeness < self.thresholds['entity_completeness_min']:
                alerts.append({
                    'type': 'low_entity_completeness',
                    'severity': 'medium',
                    'message': f"{entity_type} completeness ({completeness:.2%}) below threshold ({self.thresholds['entity_completeness_min']:.2%})",
                    'paper_id': paper_id,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Store alerts
        self.alerts.extend(alerts)
        
        # Log alerts
        for alert in alerts:
            if alert['severity'] == 'high':
                logger.error(f"⚠️ {alert['message']}")
            else:
                logger.warning(f"⚠️ {alert['message']}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            **self.metrics,
            'alerts': self.alerts[-10:],  # Last 10 alerts
            'average_extraction_time': (
                sum(self.metrics['extraction_times']) / len(self.metrics['extraction_times'])
                if self.metrics['extraction_times'] else 0.0
            )
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate quality report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_papers': self.metrics['total_papers_processed'],
                'papers_with_issues': self.metrics['papers_with_issues'],
                'extraction_success_rate': self.metrics['extraction_success_rate'],
                'average_confidence': self.metrics['average_confidence'],
                'validation_failure_rate': self.metrics['validation_failure_rate'],
                'average_extraction_time': (
                    sum(self.metrics['extraction_times']) / len(self.metrics['extraction_times'])
                    if self.metrics['extraction_times'] else 0.0
                )
            },
            'entity_completeness': dict(self.metrics['entity_completeness']),
            'error_counts': dict(self.metrics['error_counts']),
            'recent_alerts': self.alerts[-20:],  # Last 20 alerts
            'status': self._calculate_overall_status()
        }
        
        return report
    
    def _calculate_overall_status(self) -> str:
        """Calculate overall system status"""
        if (self.metrics['extraction_success_rate'] < self.thresholds['extraction_success_rate'] or
            self.metrics['validation_failure_rate'] > self.thresholds['validation_failure_rate']):
            return 'degraded'
        elif (self.metrics['average_confidence'] < self.thresholds['average_confidence']):
            return 'warning'
        else:
            return 'healthy'
    
    def print_summary(self):
        """Print quality summary to console"""
        report = self.generate_report()
        
        print("\n" + "=" * 70)
        print("QUALITY MONITORING SUMMARY")
        print("=" * 70)
        print(f"Status: {report['status'].upper()}")
        print(f"Total Papers Processed: {report['summary']['total_papers']}")
        print(f"Extraction Success Rate: {report['summary']['extraction_success_rate']:.2%}")
        print(f"Average Confidence: {report['summary']['average_confidence']:.2f}")
        print(f"Validation Failure Rate: {report['summary']['validation_failure_rate']:.2%}")
        print(f"Average Extraction Time: {report['summary']['average_extraction_time']:.1f}s")
        print("\nEntity Completeness:")
        for entity_type, completeness in report['entity_completeness'].items():
            print(f"  {entity_type}: {completeness:.2%}")
        print("\nError Counts:")
        for error_type, count in report['error_counts'].items():
            print(f"  {error_type}: {count}")
        if report['recent_alerts']:
            print(f"\nRecent Alerts ({len(report['recent_alerts'])}):")
            for alert in report['recent_alerts'][-5:]:
                print(f"  [{alert['severity'].upper()}] {alert['message']}")
        print("=" * 70 + "\n")

