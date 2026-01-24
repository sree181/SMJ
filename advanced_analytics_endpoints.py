#!/usr/bin/env python3
"""
Advanced Analytics Endpoints with Graph RAG
Sophisticated metrics for temporal analysis, topic evolution, and theoretical divergence
"""

import os
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter
from neo4j import GraphDatabase
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
# scipy imports are optional - only used for advanced clustering
try:
    from scipy.spatial.distance import pdist, squareform
    from scipy.cluster.hierarchy import linkage, fcluster
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not available - some advanced clustering features may be limited")
import math

# NetworkX for graph centrality calculations
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("networkx not available - centrality features will be limited")

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedAnalytics:
    """Advanced analytics using Graph RAG and sophisticated metrics"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
        # Initialize embedding model for topic analysis
        logger.info("Loading embedding model for analytics...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✓ Embedding model loaded")
    
    def get_paper_counts_by_interval(self, start_year: int = 1985, end_year: int = 2025) -> List[Dict]:
        """
        Get paper counts by 5-year intervals
        
        Returns:
            List of dicts with interval, count, and papers
        """
        intervals = []
        current_start = start_year
        
        while current_start < end_year:
            current_end = min(current_start + 5, end_year)
            
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (p:Paper)
                    WHERE p.year >= $start_year 
                      AND p.year < $end_year
                      AND p.year > 0
                    RETURN count(p) as count,
                           collect(p.paper_id) as paper_ids
                """, start_year=current_start, end_year=current_end)
                
                record = result.single()
                count = record['count'] if record else 0
                paper_ids = record['paper_ids'] if record else []
                
                intervals.append({
                    'interval': f"{current_start}-{current_end-1}",
                    'start_year': current_start,
                    'end_year': current_end - 1,
                    'count': count,
                    'paper_ids': paper_ids
                })
            
            current_start = current_end
        
        return intervals
    
    def get_author_counts_by_interval(self, start_year: int = 1985, end_year: int = 2025) -> List[Dict]:
        """
        Get author counts by 5-year intervals
        
        Returns:
            List of dicts with interval, total unique authors, and author details
        """
        intervals = []
        current_start = start_year
        
        while current_start < end_year:
            current_end = min(current_start + 5, end_year)
            
            with self.driver.session() as session:
                # Get distinct authors and their paper counts for this interval
                result = session.run("""
                    MATCH (p:Paper)<-[:AUTHORED]-(a:Author)
                    WHERE p.year >= $start_year 
                      AND p.year < $end_year
                      AND p.year > 0
                    WITH a, count(DISTINCT p) as paper_count
                    RETURN a.author_id as author_id,
                           a.full_name as full_name,
                           a.given_name as given_name,
                           a.family_name as family_name,
                           paper_count,
                           collect(DISTINCT p.paper_id) as paper_ids
                    ORDER BY paper_count DESC, a.family_name, a.given_name
                """, start_year=current_start, end_year=current_end)
                
                authors = []
                author_ids = []
                total_papers = 0
                
                for record in result:
                    author_data = {
                        'author_id': record['author_id'],
                        'full_name': record['full_name'] or f"{record.get('given_name', '')} {record.get('family_name', '')}".strip(),
                        'given_name': record.get('given_name', ''),
                        'family_name': record.get('family_name', ''),
                        'paper_count': record['paper_count'],
                        'paper_ids': record['paper_ids']
                    }
                    authors.append(author_data)
                    author_ids.append(record['author_id'])
                    total_papers += record['paper_count']
                
                # Get total unique author count
                unique_author_count = len(author_ids)
                
                intervals.append({
                    'interval': f"{current_start}-{current_end-1}",
                    'start_year': current_start,
                    'end_year': current_end - 1,
                    'total_authors': unique_author_count,
                    'total_papers': total_papers,
                    'authors': authors
                })
            
            current_start = current_end
        
        return intervals
    
    def calculate_topic_evolution(self, start_year: int = 1985, end_year: int = 2025) -> Dict[str, Any]:
        """
        Calculate topic evolution using embeddings and clustering
        
        Metrics:
        - Topic clusters per interval (using K-means on paper embeddings)
        - Topic coherence (average similarity within clusters)
        - Topic diversity (number of distinct topics)
        - Topic stability (similarity of topics across intervals)
        - Emerging topics (new clusters)
        - Declining topics (disappearing clusters)
        """
        intervals = self.get_paper_counts_by_interval(start_year, end_year)
        topic_evolution = []
        
        all_interval_embeddings = []
        all_interval_labels = []
        
        for interval_data in intervals:
            interval = interval_data['interval']
            paper_ids = interval_data['paper_ids']
            
            if not paper_ids:
                topic_evolution.append({
                    'interval': interval,
                    'topics': [],
                    'topic_count': 0,
                    'coherence': 0,
                    'diversity': 0,
                    'emerging_topics': [],
                    'declining_topics': []
                })
                continue
            
            # Get paper embeddings
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (p:Paper)
                    WHERE p.paper_id IN $paper_ids
                    AND p.embedding IS NOT NULL
                    RETURN p.paper_id as paper_id,
                           p.embedding as embedding,
                           p.title as title,
                           p.abstract as abstract
                """, paper_ids=paper_ids)
                
                papers = list(result)
            
            if len(papers) < 3:
                # Not enough papers for clustering
                topic_evolution.append({
                    'interval': interval,
                    'topics': [],
                    'topic_count': 0,
                    'coherence': 0,
                    'diversity': 0
                })
                continue
            
            # Extract embeddings
            embeddings = np.array([p['embedding'] for p in papers if p['embedding']])
            paper_info = [(p['paper_id'], p['title'], p['abstract']) for p in papers if p['embedding']]
            
            if len(embeddings) < 3:
                continue
            
            # Determine optimal number of clusters (elbow method simplified)
            max_clusters = min(10, len(embeddings) // 3)
            optimal_k = max(2, max_clusters)
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # Calculate topic metrics
            topics = []
            for cluster_id in range(optimal_k):
                cluster_indices = np.where(cluster_labels == cluster_id)[0]
                cluster_embeddings = embeddings[cluster_indices]
                cluster_papers = [paper_info[i] for i in cluster_indices]
                
                # Calculate coherence (average similarity within cluster)
                if len(cluster_embeddings) > 1:
                    similarities = cosine_similarity(cluster_embeddings)
                    # Remove diagonal (self-similarity)
                    mask = np.ones(similarities.shape, dtype=bool)
                    np.fill_diagonal(mask, False)
                    coherence = similarities[mask].mean()
                else:
                    coherence = 1.0
                
                # Get representative papers (closest to centroid)
                centroid = kmeans.cluster_centers_[cluster_id]
                distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
                representative_idx = cluster_indices[np.argmin(distances)]
                representative_paper = paper_info[representative_idx]
                
                topics.append({
                    'cluster_id': cluster_id,
                    'paper_count': len(cluster_papers),
                    'coherence': float(coherence),
                    'representative_paper': {
                        'paper_id': representative_paper[0],
                        'title': representative_paper[1]
                    },
                    'paper_ids': [p[0] for p in cluster_papers]
                })
            
            # Calculate diversity (entropy of cluster sizes)
            cluster_sizes = [t['paper_count'] for t in topics]
            total = sum(cluster_sizes)
            if total > 0:
                proportions = [s / total for s in cluster_sizes]
                diversity = -sum(p * math.log(p + 1e-10) for p in proportions) / math.log(len(proportions) + 1e-10)
            else:
                diversity = 0
            
            # Average coherence
            avg_coherence = sum(t['coherence'] for t in topics) / len(topics) if topics else 0
            
            topic_evolution.append({
                'interval': interval,
                'topics': topics,
                'topic_count': len(topics),
                'coherence': float(avg_coherence),
                'diversity': float(diversity),
                'total_papers': len(embeddings)
            })
            
            # Store for cross-interval analysis
            all_interval_embeddings.append(embeddings)
            all_interval_labels.append((interval, cluster_labels, kmeans.cluster_centers_))
        
        # Calculate topic stability (similarity across intervals)
        stability_metrics = self._calculate_topic_stability(all_interval_labels)
        
        # Identify emerging and declining topics
        emerging_declining = self._identify_emerging_declining_topics(all_interval_labels)
        
        # Add stability and emerging/declining to each interval
        for i, interval_data in enumerate(topic_evolution):
            if i < len(stability_metrics):
                interval_data['stability'] = stability_metrics[i]
            if i < len(emerging_declining):
                interval_data['emerging_topics'] = emerging_declining[i].get('emerging', [])
                interval_data['declining_topics'] = emerging_declining[i].get('declining', [])
        
        return {
            'intervals': topic_evolution,
            'summary': {
                'total_intervals': len(topic_evolution),
                'avg_topics_per_interval': sum(t['topic_count'] for t in topic_evolution) / len(topic_evolution) if topic_evolution else 0,
                'avg_coherence': sum(t['coherence'] for t in topic_evolution) / len(topic_evolution) if topic_evolution else 0,
                'avg_diversity': sum(t['diversity'] for t in topic_evolution) / len(topic_evolution) if topic_evolution else 0
            }
        }
    
    def _calculate_topic_stability(self, interval_labels: List[Tuple]) -> List[float]:
        """Calculate topic stability across intervals"""
        if len(interval_labels) < 2:
            return [0.0] * len(interval_labels)
        
        stability_scores = []
        
        for i in range(len(interval_labels)):
            if i == 0:
                stability_scores.append(1.0)  # First interval has no previous
                continue
            
            prev_interval, prev_labels, prev_centroids = interval_labels[i-1]
            curr_interval, curr_labels, curr_centroids = interval_labels[i]
            
            # Calculate similarity between centroids
            if len(prev_centroids) > 0 and len(curr_centroids) > 0:
                similarities = cosine_similarity(prev_centroids, curr_centroids)
                # Find best matching centroids
                max_similarities = similarities.max(axis=1)
                stability = float(max_similarities.mean())
            else:
                stability = 0.0
            
            stability_scores.append(stability)
        
        return stability_scores
    
    def _identify_emerging_declining_topics(self, interval_labels: List[Tuple]) -> List[Dict]:
        """Identify emerging and declining topics"""
        results = []
        
        for i in range(len(interval_labels)):
            emerging = []
            declining = []
            
            if i == 0:
                # First interval: all topics are emerging
                interval, labels, centroids = interval_labels[i]
                emerging = [{'cluster_id': j, 'paper_count': int((labels == j).sum())} 
                           for j in range(len(centroids))]
                results.append({'emerging': emerging, 'declining': declining})
                continue
            
            prev_interval, prev_labels, prev_centroids = interval_labels[i-1]
            curr_interval, curr_labels, curr_centroids = interval_labels[i]
            
            if len(prev_centroids) > 0 and len(curr_centroids) > 0:
                # Calculate similarity matrix
                similarities = cosine_similarity(prev_centroids, curr_centroids)
                
                # Find matching topics (similarity > 0.7)
                threshold = 0.7
                matched_prev = set()
                matched_curr = set()
                
                for prev_idx in range(len(prev_centroids)):
                    for curr_idx in range(len(curr_centroids)):
                        if similarities[prev_idx, curr_idx] > threshold:
                            matched_prev.add(prev_idx)
                            matched_curr.add(curr_idx)
                
                # Emerging: current topics not matched to previous
                for curr_idx in range(len(curr_centroids)):
                    if curr_idx not in matched_curr:
                        emerging.append({
                            'cluster_id': curr_idx,
                            'paper_count': int((curr_labels == curr_idx).sum())
                        })
                
                # Declining: previous topics not matched to current
                for prev_idx in range(len(prev_centroids)):
                    if prev_idx not in matched_prev:
                        declining.append({
                            'cluster_id': prev_idx,
                            'paper_count': int((prev_labels == prev_idx).sum())
                        })
            
            results.append({'emerging': emerging, 'declining': declining})
        
        return results
    
    def calculate_theoretical_evolution_divergence(self, start_year: int = 1985, end_year: int = 2025) -> Dict[str, Any]:
        """
        Calculate theoretical evolution and divergence using sophisticated metrics
        
        Metrics:
        - Theory diversity (Shannon entropy of theory usage)
        - Theory concentration (Gini coefficient)
        - Theory divergence (Jensen-Shannon divergence between intervals)
        - Theory emergence rate (new theories per interval)
        - Theory convergence (decreasing diversity over time)
        - Theory-phenomenon coupling strength
        - Theoretical fragmentation index
        """
        intervals = self.get_paper_counts_by_interval(start_year, end_year)
        evolution_data = []
        
        all_theory_distributions = []
        
        for interval_data in intervals:
            interval = interval_data['interval']
            paper_ids = interval_data['paper_ids']
            
            if not paper_ids:
                evolution_data.append({
                    'interval': interval,
                    'theories': {},
                    'theory_count': 0,
                    'diversity': 0,
                    'concentration': 0,
                    'emergence_rate': 0,
                    'fragmentation_index': 0
                })
                continue
            
            # Get theory usage
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                    WHERE p.paper_id IN $paper_ids
                    RETURN t.name as theory_name,
                           count(p) as usage_count,
                           collect(DISTINCT p.paper_id) as paper_ids
                """, paper_ids=paper_ids)
                
                theory_usage = {r['theory_name']: {
                    'count': r['usage_count'],
                    'paper_ids': r['paper_ids']
                } for r in result}
            
            if not theory_usage:
                evolution_data.append({
                    'interval': interval,
                    'theories': {},
                    'theory_count': 0,
                    'diversity': 0,
                    'concentration': 0,
                    'emergence_rate': 0,
                    'fragmentation_index': 0
                })
                continue
            
            # Calculate diversity (Shannon entropy)
            total_usage = sum(t['count'] for t in theory_usage.values())
            proportions = [t['count'] / total_usage for t in theory_usage.values()]
            diversity = -sum(p * math.log(p + 1e-10) for p in proportions) / math.log(len(proportions) + 1e-10)
            
            # Calculate concentration (Gini coefficient)
            sorted_counts = sorted([t['count'] for t in theory_usage.values()], reverse=True)
            n = len(sorted_counts)
            if n > 1:
                total = sum(sorted_counts)
                if total > 0:
                    # Standard Gini coefficient formula: Gini = (ΣΣ |x_i - x_j|) / (2 * n² * x̄)
                    # This measures the mean absolute difference between all pairs
                    mean = total / n
                    pairwise_diff_sum = sum(abs(xi - xj) 
                                           for i, xi in enumerate(sorted_counts) 
                                           for j, xj in enumerate(sorted_counts))
                    gini = pairwise_diff_sum / (2 * n * n * mean) if mean > 0 else 0.0
                    gini = max(0, min(1, gini))  # Clamp to [0, 1]
                else:
                    gini = 0.0
            else:
                gini = 0.0
            
            # Calculate fragmentation index (inverse of concentration)
            fragmentation = 1 - gini
            
            # Get theory-phenomenon coupling
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                    WHERE t.name IN $theory_names
                    WITH t.name as theory_name, count(DISTINCT ph) as phenomenon_count
                    RETURN theory_name, phenomenon_count
                """, theory_names=list(theory_usage.keys()))
                
                theory_phenomenon_coupling = {r['theory_name']: r['phenomenon_count'] for r in result}
            
            evolution_data.append({
                'interval': interval,
                'theories': {name: {
                    'usage_count': data['count'],
                    'paper_count': len(data['paper_ids']),
                    'phenomenon_count': theory_phenomenon_coupling.get(name, 0)
                } for name, data in theory_usage.items()},
                'theory_count': len(theory_usage),
                'diversity': float(diversity),
                'concentration': float(gini),
                'fragmentation_index': float(fragmentation),
                'total_papers': len(paper_ids)
            })
            
            # Store distribution for divergence calculation
            all_theory_distributions.append((interval, theory_usage))
        
        # Calculate divergence between intervals
        divergence_metrics = self._calculate_theory_divergence(all_theory_distributions)
        
        # Calculate emergence rate
        emergence_rates = self._calculate_emergence_rate(all_theory_distributions)
        
        # Add divergence and emergence to each interval
        for i, interval_data in enumerate(evolution_data):
            if i < len(divergence_metrics):
                interval_data['divergence'] = divergence_metrics[i]
            if i < len(emergence_rates):
                interval_data['emergence_rate'] = emergence_rates[i]
        
        return {
            'intervals': evolution_data,
            'summary': {
                'total_intervals': len(evolution_data),
                'avg_diversity': sum(e['diversity'] for e in evolution_data) / len(evolution_data) if evolution_data else 0,
                'avg_concentration': sum(e['concentration'] for e in evolution_data) / len(evolution_data) if evolution_data else 0,
                'avg_fragmentation': sum(e['fragmentation_index'] for e in evolution_data) / len(evolution_data) if evolution_data else 0,
                'trend': self._calculate_trend(evolution_data, 'diversity')
            }
        }
    
    def _calculate_theory_divergence(self, distributions: List[Tuple]) -> List[float]:
        """Calculate Jensen-Shannon divergence between intervals"""
        if len(distributions) < 2:
            return [0.0] * len(distributions)
        
        divergence_scores = []
        
        for i in range(len(distributions)):
            if i == 0:
                divergence_scores.append(0.0)
                continue
            
            prev_interval, prev_dist = distributions[i-1]
            curr_interval, curr_dist = distributions[i]
            
            # Get all unique theories
            all_theories = set(prev_dist.keys()) | set(curr_dist.keys())
            
            # Create probability distributions
            prev_total = sum(t['count'] for t in prev_dist.values())
            curr_total = sum(t['count'] for t in curr_dist.values())
            
            prev_probs = {t: prev_dist.get(t, {}).get('count', 0) / prev_total if prev_total > 0 else 0 
                         for t in all_theories}
            curr_probs = {t: curr_dist.get(t, {}).get('count', 0) / curr_total if curr_total > 0 else 0 
                         for t in all_theories}
            
            # Calculate Jensen-Shannon divergence
            p = np.array([prev_probs[t] for t in all_theories])
            q = np.array([curr_probs[t] for t in all_theories])
            
            m = 0.5 * (p + q)
            kl_pm = np.sum(p * np.log((p + 1e-10) / (m + 1e-10)))
            kl_qm = np.sum(q * np.log((q + 1e-10) / (m + 1e-10)))
            js_divergence = 0.5 * kl_pm + 0.5 * kl_qm
            
            divergence_scores.append(float(js_divergence))
        
        return divergence_scores
    
    def _calculate_emergence_rate(self, distributions: List[Tuple]) -> List[float]:
        """Calculate theory emergence rate (new theories per interval)"""
        if len(distributions) < 2:
            return [0.0] * len(distributions)
        
        emergence_rates = []
        seen_theories = set()
        
        for i, (interval, dist) in enumerate(distributions):
            if i == 0:
                # First interval: all theories are new
                new_count = len(dist)
                seen_theories.update(dist.keys())
                emergence_rates.append(float(new_count))
                continue
            
            # Count new theories
            new_theories = set(dist.keys()) - seen_theories
            new_count = len(new_theories)
            seen_theories.update(dist.keys())
            
            # Normalize by total papers in interval
            total_papers = sum(t['count'] for t in dist.values())
            rate = new_count / total_papers if total_papers > 0 else 0
            
            emergence_rates.append(float(rate))
        
        return emergence_rates
    
    def _calculate_trend(self, data: List[Dict], metric: str) -> str:
        """Calculate trend (increasing, decreasing, stable)"""
        if len(data) < 2:
            return "stable"
        
        values = [d[metric] for d in data if metric in d]
        if len(values) < 2:
            return "stable"
        
        # Simple linear regression slope
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"
    
    def calculate_theory_betweenness(self, min_phenomena: int = 2) -> Dict[str, Any]:
        """
        Calculate theory betweenness and cross-topic reach
        
        Metrics:
        - Cross-topic reach: Number of distinct phenomena each theory explains
        - Betweenness score: How theories connect different phenomena
        - Bridge theories: Theories that connect multiple phenomena clusters
        
        Args:
            min_phenomena: Minimum number of phenomena to be considered a bridge theory
        
        Returns:
            Dict with theories ranked by betweenness metrics
        """
        try:
            with self.driver.session() as session:
                # Get theory-phenomenon connections (optimized query with LIMIT)
                result = session.run("""
                    MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                    WITH t, count(DISTINCT ph) as phenomenon_count,
                         collect(DISTINCT ph.phenomenon_name) as phenomena
                    WHERE phenomenon_count >= $min_phenomena
                    RETURN t.name as theory_name,
                           phenomenon_count as cross_topic_reach,
                           phenomena
                    ORDER BY phenomenon_count DESC
                    LIMIT 100
                """, min_phenomena=min_phenomena)
                
                theories = []
                for record in result:
                    theories.append({
                        'theory_name': record['theory_name'],
                        'cross_topic_reach': record['cross_topic_reach'],
                        'phenomena': record['phenomena']
                    })
                
                # Calculate bridge score (theories connecting different phenomenon clusters)
                # For now, we'll use cross-topic reach as a proxy for betweenness
                # A more sophisticated approach would use graph centrality algorithms
                
                # Get paper counts for all theories in one query (more efficient)
                theory_names = [t['theory_name'] for t in theories]
                if theory_names:
                    paper_counts_result = session.run("""
                        MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                        WHERE t.name IN $theory_names
                        RETURN t.name as theory_name, count(p) as paper_count
                    """, theory_names=theory_names)
                    
                    paper_counts = {r['theory_name']: r['paper_count'] for r in paper_counts_result}
                    for theory in theories:
                        theory['paper_count'] = paper_counts.get(theory['theory_name'], 0)
                else:
                    for theory in theories:
                        theory['paper_count'] = 0
                
                # Calculate betweenness score (normalized cross-topic reach)
                max_reach = max([t['cross_topic_reach'] for t in theories]) if theories else 1
                for theory in theories:
                    theory['betweenness_score'] = theory['cross_topic_reach'] / max_reach if max_reach > 0 else 0
                
                return {
                    'theories': theories,
                    'summary': {
                        'total_bridge_theories': len(theories),
                        'avg_cross_topic_reach': sum(t['cross_topic_reach'] for t in theories) / len(theories) if theories else 0,
                        'max_cross_topic_reach': max([t['cross_topic_reach'] for t in theories]) if theories else 0
                    }
                }
        except Exception as e:
            logger.error(f"Error in calculate_theory_betweenness: {e}")
            return {
                'theories': [],
                'summary': {
                    'total_bridge_theories': 0,
                    'avg_cross_topic_reach': 0,
                    'max_cross_topic_reach': 0
                },
                'error': str(e)
            }
    
    def calculate_opportunity_gaps(self, max_theories: int = 2) -> Dict[str, Any]:
        """
        Calculate opportunity gap score - identify under-theorized phenomena
        
        Metrics:
        - Opportunity gap score: Phenomena with fewer than max_theories explaining them
        - Coverage breadth: Number of theories per phenomenon
        - Research opportunities: Phenomena that need more theoretical development
        
        Args:
            max_theories: Maximum number of theories to be considered "well-theorized"
        
        Returns:
            Dict with phenomena ranked by opportunity gap
        """
        with self.driver.session() as session:
            # Get phenomenon coverage (how many theories explain each phenomenon)
            result = session.run("""
                MATCH (ph:Phenomenon)
                OPTIONAL MATCH (ph)<-[:EXPLAINS_PHENOMENON]-(t:Theory)
                WITH ph, count(DISTINCT t) as theory_count,
                     collect(DISTINCT t.name) as theories
                RETURN ph.phenomenon_name as phenomenon_name,
                       theory_count,
                       theories,
                       CASE 
                           WHEN theory_count = 0 THEN 1.0
                           WHEN theory_count <= $max_theories THEN (1.0 - (theory_count / $max_theories))
                           ELSE 0.0
                       END as opportunity_gap_score
                ORDER BY opportunity_gap_score DESC, theory_count ASC
            """, max_theories=max_theories)
            
            opportunities = []
            for record in result:
                opportunities.append({
                    'phenomenon_name': record['phenomenon_name'],
                    'theory_count': record['theory_count'],
                    'theories': record['theories'],
                    'opportunity_gap_score': float(record['opportunity_gap_score'])
                })
            
            # Get paper counts for all phenomena in one query (more efficient)
            phenomenon_names = [opp['phenomenon_name'] for opp in opportunities]
            if phenomenon_names:
                paper_counts_result = session.run("""
                    MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                    WHERE ph.phenomenon_name IN $phenomenon_names
                    RETURN ph.phenomenon_name as phenomenon_name, count(p) as paper_count
                """, phenomenon_names=phenomenon_names)
                
                paper_counts = {r['phenomenon_name']: r['paper_count'] for r in paper_counts_result}
                for opp in opportunities:
                    opp['paper_count'] = paper_counts.get(opp['phenomenon_name'], 0)
            else:
                for opp in opportunities:
                    opp['paper_count'] = 0
            
            # Separate into high-opportunity and well-theorized
            high_opportunity = [o for o in opportunities if o['opportunity_gap_score'] > 0]
            well_theorized = [o for o in opportunities if o['opportunity_gap_score'] == 0]
            
            return {
                'opportunities': opportunities,
                'high_opportunity': high_opportunity[:50],  # Top 50 opportunities
                'well_theorized': well_theorized[:20],  # Top 20 well-theorized
                'summary': {
                    'total_phenomena': len(opportunities),
                    'high_opportunity_count': len(high_opportunity),
                    'well_theorized_count': len(well_theorized),
                    'avg_theory_coverage': sum(o['theory_count'] for o in opportunities) / len(opportunities) if opportunities else 0,
                    'avg_opportunity_gap': sum(o['opportunity_gap_score'] for o in opportunities) / len(opportunities) if opportunities else 0
                }
            }
    
    def calculate_integration_mechanism(self, start_year: int = 1985, end_year: int = 2025) -> Dict[str, Any]:
        """
        Calculate integration mechanism metrics
        
        Metrics:
        - Theory co-usage: Papers using multiple theories together
        - Integration score: Average theories per paper
        - Integration diversity: Shannon entropy of theory combinations
        - Integration strength: Frequency of specific theory pairs
        - Cross-domain integration: Theories spanning multiple phenomena
        
        Args:
            start_year: Start year for analysis
            end_year: End year for analysis
        
        Returns:
            Dict with integration metrics
        """
        intervals = self.get_paper_counts_by_interval(start_year, end_year)
        integration_data = []
        
        for interval_data in intervals:
            interval = interval_data['interval']
            paper_ids = interval_data['paper_ids']
            
            if not paper_ids:
                integration_data.append({
                    'interval': interval,
                    'integration_score': 0,
                    'integration_diversity': 0,
                    'theory_co_usage_pairs': [],
                    'avg_theories_per_paper': 0,
                    'papers_with_multiple_theories': 0
                })
                continue
            
            with self.driver.session() as session:
                # Get theory counts per paper
                result = session.run("""
                    MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                    WHERE p.paper_id IN $paper_ids
                    WITH p, count(DISTINCT t) as theory_count
                    RETURN avg(theory_count) as avg_theories,
                           collect(p.paper_id) as papers,
                           collect(theory_count) as theory_counts
                """, paper_ids=paper_ids)
                
                record = result.single()
                avg_theories = record['avg_theories'] if record and record['avg_theories'] else 0
                theory_counts = record['theory_counts'] if record else []
                papers_with_multiple = sum(1 for count in theory_counts if count > 1) if theory_counts else 0
                
                # Get theory co-usage pairs
                co_usage_result = session.run("""
                    MATCH (p:Paper)-[:USES_THEORY]->(t1:Theory)
                    MATCH (p)-[:USES_THEORY]->(t2:Theory)
                    WHERE p.paper_id IN $paper_ids AND t1 <> t2
                    WITH t1.name as theory1, t2.name as theory2, count(DISTINCT p) as co_usage_count
                    ORDER BY co_usage_count DESC
                    LIMIT 20
                    RETURN theory1, theory2, co_usage_count
                """, paper_ids=paper_ids)
                
                co_usage_pairs = [
                    {
                        'theory1': r['theory1'],
                        'theory2': r['theory2'],
                        'co_usage_count': r['co_usage_count']
                    }
                    for r in co_usage_result
                ]
                
                # Calculate integration diversity (Shannon entropy of theory combinations)
                # Get all unique theory combinations
                combo_result = session.run("""
                    MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                    WHERE p.paper_id IN $paper_ids
                    WITH p, collect(DISTINCT t.name) as theories
                    WHERE size(theories) > 1
                    WITH theories, count(p) as combo_count
                    RETURN combo_count
                """, paper_ids=paper_ids)
                
                combo_counts = [r['combo_count'] for r in combo_result]
                total_combos = sum(combo_counts) if combo_counts else 1
                
                if combo_counts and total_combos > 0:
                    proportions = [c / total_combos for c in combo_counts]
                    integration_diversity = -sum(p * math.log(p + 1e-10) for p in proportions) / math.log(len(proportions) + 1e-10)
                else:
                    integration_diversity = 0.0
                
                integration_data.append({
                    'interval': interval,
                    'integration_score': float(avg_theories),
                    'integration_diversity': float(integration_diversity),
                    'theory_co_usage_pairs': co_usage_pairs,
                    'avg_theories_per_paper': float(avg_theories),
                    'papers_with_multiple_theories': papers_with_multiple,
                    'total_papers': len(paper_ids)
                })
        
        # Calculate overall integration strength (top theory pairs across all intervals)
        all_co_usage = {}
        for interval_data in integration_data:
            for pair in interval_data.get('theory_co_usage_pairs', []):
                key = tuple(sorted([pair['theory1'], pair['theory2']]))
                if key not in all_co_usage:
                    all_co_usage[key] = 0
                all_co_usage[key] += pair['co_usage_count']
        
        top_pairs = sorted(
            [{'theory1': k[0], 'theory2': k[1], 'total_co_usage': v} 
             for k, v in all_co_usage.items()],
            key=lambda x: x['total_co_usage'],
            reverse=True
        )[:20]
        
        return {
            'intervals': integration_data,
            'top_integration_pairs': top_pairs,
            'summary': {
                'avg_integration_score': sum(d['integration_score'] for d in integration_data) / len(integration_data) if integration_data else 0,
                'avg_integration_diversity': sum(d['integration_diversity'] for d in integration_data) / len(integration_data) if integration_data else 0,
                'total_intervals': len(integration_data)
            }
        }
    
    def calculate_cumulative_theory(self, start_year: int = 1985, end_year: int = 2025) -> Dict[str, Any]:
        """
        Calculate lack of cumulative theory metrics
        
        Metrics:
        - Theory accumulation: How theories build on previous work
        - Cumulative knowledge: Theory-phenomenon relationship growth
        - Theory persistence: How long theories remain active
        - Knowledge accumulation rate: New theory-phenomenon connections per period
        
        Args:
            start_year: Start year for analysis
            end_year: End year for analysis
        
        Returns:
            Dict with cumulative theory metrics
        """
        intervals = self.get_paper_counts_by_interval(start_year, end_year)
        cumulative_data = []
        
        seen_theories = set()
        seen_theory_phenomenon_pairs = set()
        
        for interval_data in intervals:
            interval = interval_data['interval']
            paper_ids = interval_data['paper_ids']
            
            if not paper_ids:
                cumulative_data.append({
                    'interval': interval,
                    'new_theories': 0,
                    'cumulative_theories': 0,
                    'new_connections': 0,
                    'cumulative_connections': 0,
                    'theory_persistence': 0,
                    'accumulation_rate': 0
                })
                continue
            
            with self.driver.session() as session:
                # Get theories used in this interval
                theory_result = session.run("""
                    MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                    WHERE p.paper_id IN $paper_ids
                    RETURN DISTINCT t.name as theory_name
                """, paper_ids=paper_ids)
                
                current_theories = {r['theory_name'] for r in theory_result}
                new_theories = current_theories - seen_theories
                seen_theories.update(current_theories)
                
                # Get theory-phenomenon connections in this interval
                connection_result = session.run("""
                    MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                    WHERE EXISTS {
                        MATCH (p:Paper)-[:USES_THEORY]->(t)
                        WHERE p.paper_id IN $paper_ids
                    }
                    RETURN DISTINCT t.name as theory_name, ph.phenomenon_name as phenomenon_name
                """, paper_ids=paper_ids)
                
                current_connections = {(r['theory_name'], r['phenomenon_name']) for r in connection_result}
                new_connections = current_connections - seen_theory_phenomenon_pairs
                seen_theory_phenomenon_pairs.update(current_connections)
                
                # Calculate theory persistence (theories that appeared in previous intervals)
                if len(cumulative_data) > 0:
                    prev_theories = cumulative_data[-1].get('cumulative_theories', 0)
                    persistent_theories = len(seen_theories) - len(new_theories) if len(seen_theories) > len(new_theories) else 0
                    persistence_rate = persistent_theories / len(seen_theories) if seen_theories else 0
                else:
                    persistence_rate = 0.0
                
                # Calculate accumulation rate (new connections per paper)
                accumulation_rate = len(new_connections) / len(paper_ids) if paper_ids else 0
                
                cumulative_data.append({
                    'interval': interval,
                    'new_theories': len(new_theories),
                    'cumulative_theories': len(seen_theories),
                    'new_connections': len(new_connections),
                    'cumulative_connections': len(seen_theory_phenomenon_pairs),
                    'theory_persistence': float(persistence_rate),
                    'accumulation_rate': float(accumulation_rate),
                    'total_papers': len(paper_ids)
                })
        
        return {
            'intervals': cumulative_data,
            'summary': {
                'total_theories': len(seen_theories),
                'total_connections': len(seen_theory_phenomenon_pairs),
                'avg_accumulation_rate': sum(d['accumulation_rate'] for d in cumulative_data) / len(cumulative_data) if cumulative_data else 0,
                'avg_persistence': sum(d['theory_persistence'] for d in cumulative_data) / len(cumulative_data) if cumulative_data else 0
            }
        }
    
    def calculate_canonical_coverage_ratio(self, start_year: int = 1985, end_year: int = 2025, min_citations: int = 5) -> Dict[str, Any]:
        """
        Calculate Canonical Coverage Ratio
        
        Coverage = (# canonical papers) / (Total papers)
        Computed by year
        
        Canonical papers are identified by:
        1. Papers with canonical_problem = true/1 (if property exists), OR
        2. Papers with citation_count >= min_citations (as proxy for canonical status)
        
        Args:
            start_year: Start year for analysis
            end_year: End year for analysis
            min_citations: Minimum citations to consider a paper canonical (default: 5)
        """
        coverage_by_year = []
        
        for year in range(start_year, end_year + 1):
            with self.driver.session() as session:
                # First, check if canonical_problem property exists on any papers
                property_check = session.run("""
                    MATCH (p:Paper)
                    WHERE p.canonical_problem IS NOT NULL
                    RETURN count(p) as papers_with_property
                    LIMIT 1
                """).single()
                
                has_canonical_property = property_check and property_check['papers_with_property'] > 0
                
                if has_canonical_property:
                    # Use canonical_problem property if it exists
                    result = session.run("""
                        MATCH (p:Paper)
                        WHERE p.year = $year AND p.year > 0
                        WITH count(p) as total_papers
                        OPTIONAL MATCH (p2:Paper)
                        WHERE p2.year = $year 
                          AND p2.year > 0
                          AND (p2.canonical_problem = true OR p2.canonical_problem = 1)
                        WITH total_papers, count(p2) as canonical_papers
                        RETURN total_papers, canonical_papers,
                               CASE 
                                   WHEN total_papers > 0 THEN toFloat(canonical_papers) / toFloat(total_papers)
                                   ELSE 0.0
                               END as coverage_ratio
                    """, year=year)
                else:
                    # Use theory/phenomenon connectivity as proxy for canonical papers
                    # Canonical papers are those that connect to multiple theories or phenomena
                    result = session.run("""
                        MATCH (p:Paper)
                        WHERE p.year = $year AND p.year > 0
                        WITH count(p) as total_papers
                        MATCH (p2:Paper)
                        WHERE p2.year = $year AND p2.year > 0
                        OPTIONAL MATCH (p2)-[:USES_THEORY]->(t:Theory)
                        OPTIONAL MATCH (p2)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                        WITH total_papers, p2, 
                             count(DISTINCT t) as theory_count,
                             count(DISTINCT ph) as phenomenon_count
                        WITH total_papers, p2, (theory_count + phenomenon_count) as total_connections
                        WHERE total_connections >= $min_citations
                        WITH total_papers, count(DISTINCT p2) as canonical_papers
                        RETURN total_papers, canonical_papers,
                               CASE 
                                   WHEN total_papers > 0 THEN toFloat(canonical_papers) / toFloat(total_papers)
                                   ELSE 0.0
                               END as coverage_ratio
                    """, year=year, min_citations=min_citations)
                
                record = result.single()
                if record:
                    coverage_by_year.append({
                        'year': year,
                        'total_papers': record['total_papers'],
                        'canonical_papers': record['canonical_papers'],
                        'coverage_ratio': float(record['coverage_ratio'])
                    })
                else:
                    coverage_by_year.append({
                        'year': year,
                        'total_papers': 0,
                        'canonical_papers': 0,
                        'coverage_ratio': 0.0
                    })
        
        # Filter out years with no papers for summary calculation
        years_with_papers = [d for d in coverage_by_year if d['total_papers'] > 0]
        
        return {
            'coverage_by_year': coverage_by_year,
            'summary': {
                'avg_coverage': sum(d['coverage_ratio'] for d in years_with_papers) / len(years_with_papers) if years_with_papers else 0,
                'total_canonical_papers': sum(d['canonical_papers'] for d in coverage_by_year),
                'total_papers': sum(d['total_papers'] for d in coverage_by_year),
                'method': 'canonical_problem_property' if has_canonical_property else 'theory_phenomenon_connectivity',
                'min_connections': min_citations if not has_canonical_property else None
            }
        }
    
    def calculate_canonical_centrality(self) -> Dict[str, Any]:
        """
        Calculate Canonical Centrality
        
        1. Subgraph = canonical papers
        2. Compute eigenvector centrality and PageRank
        3. Compare to non-canonical papers
        
        Requires NetworkX
        """
        if not NETWORKX_AVAILABLE:
            return {
                'error': 'NetworkX not available. Install with: pip install networkx',
                'canonical_centrality': {},
                'non_canonical_centrality': {}
            }
        
        # Build graph from Neo4j
        G = nx.DiGraph()
        canonical_papers = set()
        non_canonical_papers = set()
        
        with self.driver.session() as session:
            # Get all papers and their canonical status
            papers = session.run("""
                MATCH (p:Paper)
                WHERE p.paper_id IS NOT NULL
                RETURN p.paper_id as paper_id,
                       CASE 
                           WHEN p.canonical_problem = true OR p.canonical_problem = 1 THEN true
                           ELSE false
                       END as is_canonical
            """).data()
            
            for paper in papers:
                paper_id = paper['paper_id']
                G.add_node(paper_id)
                if paper['is_canonical']:
                    canonical_papers.add(paper_id)
                else:
                    non_canonical_papers.add(paper_id)
            
            # Get paper-to-paper relationships (citations, similarity, etc.)
            relationships = session.run("""
                MATCH (p1:Paper)-[r]->(p2:Paper)
                WHERE p1.paper_id IS NOT NULL AND p2.paper_id IS NOT NULL
                RETURN p1.paper_id as source, p2.paper_id as target
            """).data()
            
            for rel in relationships:
                G.add_edge(rel['source'], rel['target'])
        
        # Create canonical subgraph
        canonical_subgraph = G.subgraph(canonical_papers)
        non_canonical_subgraph = G.subgraph(non_canonical_papers)
        
        # Compute centrality for canonical papers
        canonical_eigenvector = {}
        canonical_pagerank = {}
        if canonical_subgraph.number_of_nodes() > 0:
            try:
                canonical_eigenvector = nx.eigenvector_centrality(canonical_subgraph, max_iter=1000)
                canonical_pagerank = nx.pagerank(canonical_subgraph)
            except Exception as e:
                logger.warning(f"Error computing canonical centrality: {e}")
        
        # Compute centrality for non-canonical papers
        non_canonical_eigenvector = {}
        non_canonical_pagerank = {}
        if non_canonical_subgraph.number_of_nodes() > 0:
            try:
                non_canonical_eigenvector = nx.eigenvector_centrality(non_canonical_subgraph, max_iter=1000)
                non_canonical_pagerank = nx.pagerank(non_canonical_subgraph)
            except Exception as e:
                logger.warning(f"Error computing non-canonical centrality: {e}")
        
        # Calculate averages for comparison
        avg_canonical_eigenvector = sum(canonical_eigenvector.values()) / len(canonical_eigenvector) if canonical_eigenvector else 0
        avg_canonical_pagerank = sum(canonical_pagerank.values()) / len(canonical_pagerank) if canonical_pagerank else 0
        avg_non_canonical_eigenvector = sum(non_canonical_eigenvector.values()) / len(non_canonical_eigenvector) if non_canonical_eigenvector else 0
        avg_non_canonical_pagerank = sum(non_canonical_pagerank.values()) / len(non_canonical_pagerank) if non_canonical_pagerank else 0
        
        return {
            'canonical_centrality': {
                'eigenvector': {k: float(v) for k, v in canonical_eigenvector.items()},
                'pagerank': {k: float(v) for k, v in canonical_pagerank.items()},
                'avg_eigenvector': float(avg_canonical_eigenvector),
                'avg_pagerank': float(avg_canonical_pagerank),
                'paper_count': len(canonical_papers)
            },
            'non_canonical_centrality': {
                'eigenvector': {k: float(v) for k, v in non_canonical_eigenvector.items()},
                'pagerank': {k: float(v) for k, v in non_canonical_pagerank.items()},
                'avg_eigenvector': float(avg_non_canonical_eigenvector),
                'avg_pagerank': float(avg_non_canonical_pagerank),
                'paper_count': len(non_canonical_papers)
            },
            'comparison': {
                'eigenvector_ratio': avg_canonical_eigenvector / avg_non_canonical_eigenvector if avg_non_canonical_eigenvector > 0 else 0,
                'pagerank_ratio': avg_canonical_pagerank / avg_non_canonical_pagerank if avg_non_canonical_pagerank > 0 else 0
            }
        }
    
    def calculate_theoretical_concentration_index(self, start_year: int = 1985, end_year: int = 2025) -> Dict[str, Any]:
        """
        Calculate Theoretical Concentration Index (HHI - Herfindahl-Hirschman Index)
        
        HHI = Σ(share_i)²
        where share_i = usage_count_i / total_usage
        
        Interpretation:
        - High HHI → dominance (few theories dominate)
        - Low HHI → fragmentation (theories more evenly distributed)
        """
        intervals = self.get_paper_counts_by_interval(start_year, end_year)
        hhi_data = []
        
        for interval_data in intervals:
            interval = interval_data['interval']
            paper_ids = interval_data['paper_ids']
            
            if not paper_ids:
                hhi_data.append({
                    'interval': interval,
                    'hhi': 0.0,
                    'theory_count': 0,
                    'interpretation': 'no_data'
                })
                continue
            
            with self.driver.session() as session:
                # Get theory usage counts
                result = session.run("""
                    MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                    WHERE p.paper_id IN $paper_ids
                    RETURN t.name as theory_name, count(p) as usage_count
                """, paper_ids=paper_ids)
                
                theory_usage = {r['theory_name']: r['usage_count'] for r in result}
            
            if not theory_usage:
                hhi_data.append({
                    'interval': interval,
                    'hhi': 0.0,
                    'theory_count': 0,
                    'interpretation': 'no_data'
                })
                continue
            
            # Calculate HHI
            total_usage = sum(theory_usage.values())
            shares = [count / total_usage for count in theory_usage.values()]
            hhi = sum(share ** 2 for share in shares)
            
            # Interpretation
            if hhi > 0.25:
                interpretation = 'high_concentration'
            elif hhi > 0.15:
                interpretation = 'moderate_concentration'
            else:
                interpretation = 'fragmented'
            
            hhi_data.append({
                'interval': interval,
                'hhi': float(hhi),
                'theory_count': len(theory_usage),
                'total_usage': total_usage,
                'interpretation': interpretation,
                'top_theories': sorted(
                    [(name, count) for name, count in theory_usage.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            })
        
        return {
            'intervals': hhi_data,
            'summary': {
                'avg_hhi': sum(d['hhi'] for d in hhi_data) / len(hhi_data) if hhi_data else 0,
                'trend': self._calculate_trend(hhi_data, 'hhi')
            }
        }
    
    def calculate_theory_problem_alignment(self) -> Dict[str, Any]:
        """
        Calculate Theory-Problem Alignment Score
        
        Measures how well theories align with problems (phenomena).
        Higher alignment = theories that explain many phenomena
        
        Note: Interpreting "problem" as "phenomenon" based on available data
        """
        with self.driver.session() as session:
            # Get theory-phenomenon alignment
            result = session.run("""
                MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                WITH t, count(DISTINCT ph) as phenomenon_count,
                     collect(DISTINCT ph.phenomenon_name) as phenomena
                RETURN t.name as theory_name,
                       phenomenon_count as alignment_score,
                       phenomena
                ORDER BY phenomenon_count DESC
            """)
            
            alignments = []
            for record in result:
                alignments.append({
                    'theory_name': record['theory_name'],
                    'alignment_score': record['alignment_score'],
                    'phenomena': record['phenomena']
                })
            
            # Get paper counts for all theories in one query (more efficient)
            theory_names = [a['theory_name'] for a in alignments]
            if theory_names:
                paper_counts_result = session.run("""
                    MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                    WHERE t.name IN $theory_names
                    RETURN t.name as theory_name, count(p) as paper_count
                """, theory_names=theory_names)
                
                paper_counts = {r['theory_name']: r['paper_count'] for r in paper_counts_result}
                for alignment in alignments:
                    alignment['paper_count'] = paper_counts.get(alignment['theory_name'], 0)
            else:
                for alignment in alignments:
                    alignment['paper_count'] = 0
            
            return {
                'alignments': alignments,
                'summary': {
                    'total_theories': len(alignments),
                    'avg_alignment': sum(a['alignment_score'] for a in alignments) / len(alignments) if alignments else 0,
                    'max_alignment': max([a['alignment_score'] for a in alignments]) if alignments else 0
                }
            }
    
    def calculate_integrative_theory_centrality(self) -> Dict[str, Any]:
        """
        Calculate Integrative Theory Centrality
        
        1. Identify papers using each theory
        2. Compute betweenness centrality of those papers
        3. Average per theory
        
        Requires NetworkX for betweenness centrality
        """
        if not NETWORKX_AVAILABLE:
            return {
                'error': 'NetworkX not available. Install with: pip install networkx',
                'theory_centrality': {}
            }
        
        # Build graph from Neo4j
        G = nx.DiGraph()
        theory_papers = defaultdict(set)  # theory_name -> set of paper_ids
        
        with self.driver.session() as session:
            # Get all papers
            papers = session.run("""
                MATCH (p:Paper)
                WHERE p.paper_id IS NOT NULL
                RETURN p.paper_id as paper_id
            """).data()
            
            for paper in papers:
                G.add_node(paper['paper_id'])
            
            # Get paper-to-paper relationships
            # Since there are no direct CITES relationships, create edges based on shared theories/phenomena
            # Papers are connected if they share theories or study the same phenomena
            relationships = session.run("""
                // Papers connected through shared theories
                MATCH (p1:Paper)-[:USES_THEORY]->(t:Theory)<-[:USES_THEORY]-(p2:Paper)
                WHERE p1.paper_id IS NOT NULL AND p2.paper_id IS NOT NULL AND p1.paper_id <> p2.paper_id
                RETURN DISTINCT p1.paper_id as source, p2.paper_id as target
                UNION
                // Papers connected through shared phenomena
                MATCH (p1:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)<-[:STUDIES_PHENOMENON]-(p2:Paper)
                WHERE p1.paper_id IS NOT NULL AND p2.paper_id IS NOT NULL AND p1.paper_id <> p2.paper_id
                RETURN DISTINCT p1.paper_id as source, p2.paper_id as target
            """).data()
            
            for rel in relationships:
                G.add_edge(rel['source'], rel['target'])
            
            # Get theory-paper mappings
            theory_mappings = session.run("""
                MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                WHERE p.paper_id IS NOT NULL
                RETURN t.name as theory_name, p.paper_id as paper_id
            """).data()
            
            for mapping in theory_mappings:
                theory_papers[mapping['theory_name']].add(mapping['paper_id'])
        
        # Compute betweenness centrality for all papers
        try:
            betweenness = nx.betweenness_centrality(G)
        except Exception as e:
            logger.error(f"Error computing betweenness centrality: {e}")
            return {
                'error': str(e),
                'theory_centrality': {}
            }
        
        # Calculate average betweenness per theory
        theory_centrality = {}
        for theory_name, paper_set in theory_papers.items():
            if paper_set:
                theory_betweenness_values = [betweenness.get(paper_id, 0) for paper_id in paper_set if paper_id in betweenness]
                if theory_betweenness_values:
                    avg_betweenness = sum(theory_betweenness_values) / len(theory_betweenness_values)
                    theory_centrality[theory_name] = {
                        'avg_betweenness': float(avg_betweenness),
                        'paper_count': len(paper_set),
                        'papers_with_centrality': len(theory_betweenness_values)
                    }
        
        # Sort by average betweenness
        sorted_theories = sorted(
            theory_centrality.items(),
            key=lambda x: x[1]['avg_betweenness'],
            reverse=True
        )
        
        return {
            'theory_centrality': {
                theory: data for theory, data in sorted_theories
            },
            'summary': {
                'total_theories': len(theory_centrality),
                'avg_betweenness': sum(d['avg_betweenness'] for d in theory_centrality.values()) / len(theory_centrality) if theory_centrality else 0,
                'max_betweenness': max([d['avg_betweenness'] for d in theory_centrality.values()]) if theory_centrality else 0
            }
        }
    
    def close(self):
        self.driver.close()

# FastAPI endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Global analytics instance (lazy initialization)
_analytics_instance = None

def get_analytics():
    """Lazy initialization of analytics"""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = AdvancedAnalytics()
    return _analytics_instance

@router.get("/papers/by-interval")
async def get_paper_counts_by_interval(start_year: int = 1985, end_year: int = 2025):
    """Get paper counts by 5-year intervals"""
    try:
        analytics = get_analytics()
        intervals = analytics.get_paper_counts_by_interval(start_year, end_year)
        return {"intervals": intervals}
    except Exception as e:
        logger.error(f"Error getting paper counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/authors/by-interval")
async def get_author_counts_by_interval(start_year: int = 1985, end_year: int = 2025):
    """Get author counts by 5-year intervals"""
    try:
        analytics = get_analytics()
        intervals = analytics.get_author_counts_by_interval(start_year, end_year)
        return {"intervals": intervals}
    except Exception as e:
        logger.error(f"Error getting author counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/topics/evolution")
async def get_topic_evolution(start_year: int = 1985, end_year: int = 2025):
    """Get topic evolution metrics"""
    try:
        analytics = get_analytics()
        evolution = analytics.calculate_topic_evolution(start_year, end_year)
        return evolution
    except Exception as e:
        logger.error(f"Error calculating topic evolution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/theories/evolution-divergence")
async def get_theory_evolution_divergence(start_year: int = 1985, end_year: int = 2025):
    """Get theoretical evolution and divergence metrics"""
    try:
        analytics = get_analytics()
        evolution = analytics.calculate_theoretical_evolution_divergence(start_year, end_year)
        return evolution
    except Exception as e:
        logger.error(f"Error calculating theory evolution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/theories/betweenness")
async def get_theory_betweenness(min_phenomena: int = 2):
    """Get theory betweenness and cross-topic reach metrics"""
    try:
        analytics = get_analytics()
        betweenness = analytics.calculate_theory_betweenness(min_phenomena=min_phenomena)
        # If there's an error in the result, return it gracefully
        if 'error' in betweenness:
            logger.warning(f"Theory betweenness calculation had issues: {betweenness.get('error')}")
        return betweenness
    except Exception as e:
        logger.error(f"Error calculating theory betweenness: {e}")
        # Return empty result instead of raising exception
        return {
            'theories': [],
            'summary': {
                'total_bridge_theories': 0,
                'avg_cross_topic_reach': 0,
                'max_cross_topic_reach': 0
            },
            'error': str(e)
        }

@router.get("/phenomena/opportunity-gaps")
async def get_opportunity_gaps(max_theories: int = 2):
    """Get opportunity gap scores for under-theorized phenomena"""
    try:
        analytics = get_analytics()
        gaps = analytics.calculate_opportunity_gaps(max_theories=max_theories)
        return gaps
    except Exception as e:
        logger.error(f"Error calculating opportunity gaps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integration/mechanism")
async def get_integration_mechanism(start_year: int = 1985, end_year: int = 2025):
    """Get integration mechanism metrics (theory co-usage, integration scores)"""
    try:
        analytics = get_analytics()
        integration = analytics.calculate_integration_mechanism(start_year, end_year)
        return integration
    except Exception as e:
        logger.error(f"Error calculating integration mechanism: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/theories/cumulative")
async def get_cumulative_theory(start_year: int = 1985, end_year: int = 2025):
    """Get cumulative theory metrics (knowledge accumulation, theory persistence)"""
    try:
        analytics = get_analytics()
        cumulative = analytics.calculate_cumulative_theory(start_year, end_year)
        return cumulative
    except Exception as e:
        logger.error(f"Error calculating cumulative theory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/canonical/coverage")
async def get_canonical_coverage(start_year: int = 1985, end_year: int = 2025):
    """Get canonical coverage ratio by year"""
    try:
        analytics = get_analytics()
        coverage = analytics.calculate_canonical_coverage_ratio(start_year, end_year)
        return coverage
    except Exception as e:
        logger.error(f"Error calculating canonical coverage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/canonical/centrality")
async def get_canonical_centrality():
    """Get canonical centrality (eigenvector and PageRank)"""
    try:
        analytics = get_analytics()
        centrality = analytics.calculate_canonical_centrality()
        return centrality
    except Exception as e:
        logger.error(f"Error calculating canonical centrality: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# COMMENTED OUT - Causing 404 errors
# @router.get("/theories/concentration-index")
# async def get_theoretical_concentration(start_year: int = 1985, end_year: int = 2025):
#     """Get theoretical concentration index (HHI)"""
#     try:
#         analytics = get_analytics()
#         hhi = analytics.calculate_theoretical_concentration_index(start_year, end_year)
#         return hhi
#     except Exception as e:
#         logger.error(f"Error calculating theoretical concentration: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# COMMENTED OUT - Causing 404 errors
# COMMENTED OUT - Causing syntax errors
# @router.get("/theories/problem-alignment")
# async def get_theory_problem_alignment():
#     """Get theory-problem alignment scores
#     
#     Measures how well theories align with phenomena (problems).
#     Higher alignment score = theory explains more distinct phenomena.
#     """
#     try:
#         analytics = get_analytics()
#         alignment = analytics.calculate_theory_problem_alignment()
#         return alignment
#     except Exception as e:
#         logger.error(f"Error calculating theory-problem alignment: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# COMMENTED OUT - Causing UI errors
# @router.get("/theories/integrative-centrality")
# async def get_integrative_theory_centrality():
#     """Get integrative theory centrality (betweenness of papers using each theory)
#     
#     Calculates the average betweenness centrality of papers using each theory.
#     Higher centrality = theory is used in papers that bridge different research areas.
#     Requires NetworkX library.
#     """
#     try:
#         analytics = get_analytics()
#         centrality = analytics.calculate_integrative_theory_centrality()
#         return centrality
#     except Exception as e:
#         logger.error(f"Error calculating integrative theory centrality: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
