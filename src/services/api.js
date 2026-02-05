/**
 * API Service Layer
 * Handles all API calls to the FastAPI backend
 */

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

class ApiService {
  /**
   * Generic fetch wrapper with error handling
   */
  async fetch(endpoint, options = {}) {
    try {
      const url = `${API_BASE}${endpoint}`;
      console.log('API Request:', url, options.method || 'GET');
      
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error Response:', response.status, errorText);
        throw new Error(`API error: ${response.status} ${response.statusText} - ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      // Provide more helpful error message
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        throw new Error('Cannot connect to backend server. Make sure the API server is running on http://localhost:5000');
      }
      throw error;
    }
  }

  /**
   * Health check
   */
  async healthCheck() {
    return this.fetch('/health');
  }

  /**
   * Get statistics
   */
  async getStats() {
    return this.fetch('/stats');
  }

  /**
   * Search papers
   * @param {string} query - Search query
   * @param {object} filters - Optional filters (year, theory, method)
   */
  async searchPapers(query, filters = {}) {
    return this.fetch('/search', {
      method: 'POST',
      body: JSON.stringify({ query, ...filters }),
    });
  }

  /**
   * Get paper by ID
   * @param {string} paperId - Paper ID
   */
  async getPaper(paperId) {
    return this.fetch(`/papers/${paperId}`);
  }

  /**
   * Query GraphRAG system
   * @param {string} query - Natural language query
   * @param {string|null} persona - Optional persona: 'historian', 'reviewer2', 'advisor', 'strategist'
   */
  async queryGraphRAG(query, persona = null) {
    const body = { query };
    if (persona) {
      body.persona = persona;
    }
    return this.fetch('/query', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /**
   * Get temporal evolution data
   * @param {string} entityType - 'theory' or 'method'
   * @param {string} period - Time period (e.g., '2020-2024')
   */
  async getTemporalEvolution(entityType, period) {
    return this.fetch(`/temporal/evolution?entity=${entityType}&period=${period}`);
  }

  /**
   * Get graph data for a paper
   * @param {string} paperId - Paper ID
   */
  async getGraphData(paperId) {
    return this.fetch(`/graph/${paperId}`);
  }

  /**
   * Get knowledge metrics for an entity (theory, method, or phenomenon)
   * @param {string} entityType - 'theory', 'method', or 'phenomenon'
   * @param {string} entityName - Name of the entity
   */
  async getKnowledgeMetrics(entityType, entityName) {
    // URL encode the entity name to handle spaces and special characters
    const encodedName = encodeURIComponent(entityName);
    return this.fetch(`/metrics/${entityType}/${encodedName}`);
  }

  /**
   * Search for theories
   * @param {string} query - Search query
   * @param {number} limit - Maximum results (default: 20)
   */
  async searchTheories(query, limit = 20) {
    return this.fetch(`/theories/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  }

  /**
   * Search for methods
   * @param {string} query - Search query
   * @param {number} limit - Maximum results (default: 20)
   */
  async searchMethods(query, limit = 20) {
    return this.fetch(`/methods/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  }

  /**
   * Search for phenomena
   * @param {string} query - Search query
   * @param {number} limit - Maximum results (default: 20)
   */
  async searchPhenomena(query, limit = 20) {
    return this.fetch(`/phenomena/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  }

  /**
   * List all theories with pagination
   * @param {number} limit - Results per page (default: 50)
   * @param {number} offset - Offset for pagination (default: 0)
   * @param {string} sortBy - Sort by: 'paper_count', 'name', 'phenomenon_count' (default: 'paper_count')
   */
  async listTheories(limit = 50, offset = 0, sortBy = 'paper_count') {
    return this.fetch(`/theories?limit=${limit}&offset=${offset}&sort_by=${sortBy}`);
  }

  /**
   * Compare multiple theories
   * @param {string[]} theories - Array of theory names to compare
   * @param {string|null} query - Optional user question for context
   */
  async compareTheories(theories, query = null) {
    const body = { theories };
    if (query) {
      body.query = query;
    }
    return this.fetch('/theories/compare', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /**
   * Get full context for a theory
   * @param {string} theoryName - Name of the theory
   */
  async getTheoryContext(theoryName) {
    const encodedName = encodeURIComponent(theoryName);
    return this.fetch(`/theories/${encodedName}/context`);
  }

  /**
   * Get contribution opportunities
   * @param {object} filters - Filters: {query, type, min_potential, limit}
   */
  async getContributionOpportunities(filters = {}) {
    const params = new URLSearchParams();
    if (filters.query) params.append('query', filters.query);
    if (filters.type) params.append('type', filters.type);
    if (filters.min_potential) params.append('min_potential', filters.min_potential);
    if (filters.limit) params.append('limit', filters.limit);
    
    const queryString = params.toString();
    return this.fetch(`/contributions/opportunities${queryString ? '?' + queryString : ''}`);
  }

  /**
   * Get trend analysis for an entity
   * @param {string} entityType - 'theory', 'method', or 'phenomenon'
   * @param {string} entityName - Name of the entity
   * @param {string|null} period - Optional specific period to analyze
   */
  async getTrendAnalysis(entityType, entityName, period = null) {
    const encodedName = encodeURIComponent(entityName);
    const params = new URLSearchParams();
    if (period) params.append('period', period);
    
    const queryString = params.toString();
    return this.fetch(`/trends/${entityType}/${encodedName}${queryString ? '?' + queryString : ''}`);
  }

  /**
   * Advanced Analytics - Paper counts by 5-year intervals
   * @param {number} startYear - Start year (default: 1985)
   * @param {number} endYear - End year (default: 2026)
   */
  async getPaperCountsByInterval(startYear = 1985, endYear = 2026) {
    return this.fetch(`/analytics/papers/by-interval?start_year=${startYear}&end_year=${endYear}`);
  }

  /**
   * Advanced Analytics - Author counts by 5-year intervals
   * @param {number} startYear - Start year (default: 1985)
   * @param {number} endYear - End year (default: 2025)
   */
  async getAuthorCountsByInterval(startYear = 1985, endYear = 2025) {
    return this.fetch(`/analytics/authors/by-interval?start_year=${startYear}&end_year=${endYear}`);
  }

  /**
   * Advanced Analytics - Phenomenon counts by 5-year intervals
   * @param {number} startYear - Start year (default: 1985)
   * @param {number} endYear - End year (default: 2025)
   * @param {number} topN - Top N phenomena to return (default: 20)
   */
  async getPhenomenonCountsByInterval(startYear = 1985, endYear = 2025, topN = 20) {
    return this.fetch(`/analytics/phenomena/by-interval?start_year=${startYear}&end_year=${endYear}&top_n=${topN}`);
  }

  /**
   * Advanced Analytics - Topic evolution
   * @param {number} startYear - Start year (default: 1985)
   * @param {number} endYear - End year (default: 2025)
   */
  async getTopicEvolution(startYear = 1985, endYear = 2025) {
    return this.fetch(`/analytics/topics/evolution?start_year=${startYear}&end_year=${endYear}`);
  }

  /**
   * Advanced Analytics - Theory evolution and divergence
   * @param {number} startYear - Start year (default: 1985)
   * @param {number} endYear - End year (default: 2025)
   */
  async getTheoryEvolutionDivergence(startYear = 1985, endYear = 2025) {
    return this.fetch(`/analytics/theories/evolution-divergence?start_year=${startYear}&end_year=${endYear}`);
  }

  /**
   * Advanced Analytics - Theory betweenness and cross-topic reach
   * @param {number} minPhenomena - Minimum number of phenomena (default: 2)
   */
  async getTheoryBetweenness(minPhenomena = 2) {
    return this.fetch(`/analytics/theories/betweenness?min_phenomena=${minPhenomena}`);
  }

  /**
   * Advanced Analytics - Opportunity gap scores
   * @param {number} maxTheories - Maximum theories to be considered well-theorized (default: 2)
   */
  async getOpportunityGaps(maxTheories = 2) {
    return this.fetch(`/analytics/phenomena/opportunity-gaps?max_theories=${maxTheories}`);
  }

  /**
   * Advanced Analytics - Integration mechanism (theory co-usage)
   * @param {number} startYear - Start year (default: 1985)
   * @param {number} endYear - End year (default: 2025)
   */
  async getIntegrationMechanism(startYear = 1985, endYear = 2025) {
    return this.fetch(`/analytics/integration/mechanism?start_year=${startYear}&end_year=${endYear}`);
  }

  /**
   * Advanced Analytics - Cumulative theory (knowledge accumulation)
   * @param {number} startYear - Start year (default: 1985)
   * @param {number} endYear - End year (default: 2025)
   */
  async getCumulativeTheory(startYear = 1985, endYear = 2025) {
    return this.fetch(`/analytics/theories/cumulative?start_year=${startYear}&end_year=${endYear}`);
  }

  /**
   * Canonical Coverage Ratio - ratio of canonical papers by year
   * @param {number} startYear - Start year (default: 1985)
   * @param {number} endYear - End year (default: 2025)
   */
  async getCanonicalCoverage(startYear = 1985, endYear = 2025) {
    return this.fetch(`/analytics/canonical/coverage?start_year=${startYear}&end_year=${endYear}`);
  }

  /**
   * Canonical Centrality - eigenvector and PageRank for canonical papers
   */
  async getCanonicalCentrality() {
    return this.fetch('/analytics/canonical/centrality');
  }

  /**
   * Theoretical Concentration Index (HHI)
   * @param {number} startYear - Start year (default: 1985)
   * @param {number} endYear - End year (default: 2025)
   */
  async getTheoreticalConcentration(startYear = 1985, endYear = 2025) {
    return this.fetch(`/analytics/theories/concentration-index?start_year=${startYear}&end_year=${endYear}`);
  }

  /**
   * Theory-Problem Alignment Score
   */
  async getTheoryProblemAlignment() {
    return this.fetch('/analytics/theories/problem-alignment');
  }

  /**
   * Integrative Theory Centrality - betweenness centrality per theory
   */
  async getIntegrativeTheoryCentrality() {
    return this.fetch('/analytics/theories/integrative-centrality');
  }
}

export default new ApiService();

