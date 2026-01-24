import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import SearchBar from '../common/SearchBar';
import MetricsCard from '../common/MetricsCard';
import Loading from '../common/Loading';
import api from '../../services/api';

const MetricsDashboard = () => {
  const { entityType, entityName } = useParams();
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [showSearch, setShowSearch] = useState(!entityName);

  // Decode entity name from URL
  const decodedEntityName = entityName ? decodeURIComponent(entityName) : null;

  useEffect(() => {
    if (entityType && decodedEntityName) {
      loadMetrics(entityType, decodedEntityName);
    }
  }, [entityType, decodedEntityName]);

  const loadMetrics = async (type, name) => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getKnowledgeMetrics(type, name);
      setMetrics(data);
      setShowSearch(false);
    } catch (err) {
      console.error('Error loading metrics:', err);
      setError(`Failed to load metrics: ${err.message}`);
      setMetrics(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (query) => {
    if (!query.trim()) return;

    try {
      setLoading(true);
      setError(null);

      // Determine entity type from current route or default to theory
      const type = entityType || 'theory';
      
      let results = [];
      if (type === 'theory') {
        const data = await api.searchTheories(query);
        results = data.theories || [];
      } else if (type === 'method') {
        const data = await api.searchMethods(query);
        results = data.methods || [];
      } else if (type === 'phenomenon') {
        const data = await api.searchPhenomena(query);
        results = data.phenomena || [];
      }

      setSearchResults(results);
      setShowSearch(true);
    } catch (err) {
      console.error('Search error:', err);
      setError(`Search failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleEntitySelect = (name) => {
    const type = entityType || 'theory';
    navigate(`/metrics/${type}/${encodeURIComponent(name)}`);
  };

  const renderMetrics = () => {
    if (!metrics) return null;

    const { entity, metrics: metricData, narrative, supportingData } = metrics;
    const isTheory = entity.type === 'theory';
    const isMethod = entity.type === 'method';
    const isPhenomenon = entity.type === 'phenomenon';

    return (
      <div className="space-y-8">
        {/* Entity Header */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center space-x-3 mb-2">
                <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold uppercase">
                  {entity.type}
                </span>
                {entity.normalized && (
                  <span className="text-xs text-gray-500">
                    Normalized from: {entity.originalName}
                  </span>
                )}
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{entity.name}</h1>
            </div>
            <button
              onClick={() => setShowSearch(true)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Search Another
            </button>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Theory Metrics */}
          {isTheory && (
            <>
              {metricData.momentum !== undefined && (
                <MetricsCard
                  label="Momentum"
                  value={metricData.momentum}
                  description="Usage trend: positive = growing, negative = declining"
                  color={metricData.momentum > 0.1 ? 'green' : metricData.momentum < -0.1 ? 'red' : 'gray'}
                  trend={metricData.momentum * 100}
                />
              )}
              {metricData.evidenceStrength && (
                <>
                  <MetricsCard
                    label="Avg Connection Strength"
                    value={metricData.evidenceStrength.avgConnectionStrength}
                    description="Average strength of connections to phenomena"
                    color="blue"
                  />
                  <MetricsCard
                    label="Phenomenon Diversity"
                    value={metricData.diversity || metricData.evidenceStrength.phenomenonCount}
                    description="Number of distinct phenomena explained"
                    color="purple"
                  />
                </>
              )}
              {supportingData?.total_papers !== undefined && (
                <MetricsCard
                  label="Total Papers"
                  value={supportingData.total_papers}
                  description={`Used in ${supportingData.total_papers} papers`}
                  color="indigo"
                />
              )}
            </>
          )}

          {/* Method Metrics */}
          {isMethod && (
            <>
              {metricData.momentum !== undefined && (
                <MetricsCard
                  label="Momentum"
                  value={metricData.momentum}
                  description="Usage trend over time"
                  color={metricData.momentum > 0.1 ? 'green' : metricData.momentum < -0.1 ? 'red' : 'gray'}
                  trend={metricData.momentum * 100}
                />
              )}
              {metricData.obsolescence !== undefined && (
                <MetricsCard
                  label="Obsolescence"
                  value={metricData.obsolescence}
                  description="Decline rate (if negative momentum)"
                  color={metricData.obsolescence > 0.2 ? 'red' : 'amber'}
                />
              )}
              {metricData.adoptionRate !== undefined && (
                <MetricsCard
                  label="Adoption Rate"
                  value={metricData.adoptionRate}
                  unit="papers/year"
                  description="Average papers per year"
                  color="green"
                />
              )}
              {supportingData?.total_papers !== undefined && (
                <MetricsCard
                  label="Total Papers"
                  value={supportingData.total_papers}
                  description={`Used in ${supportingData.total_papers} papers`}
                  color="indigo"
                />
              )}
            </>
          )}

          {/* Phenomenon Metrics */}
          {isPhenomenon && (
            <>
              {metricData.hotness !== undefined && (
                <MetricsCard
                  label="Hotness Score"
                  value={metricData.hotness}
                  description="Recent research activity + diversity"
                  color={metricData.hotness > 5 ? 'green' : metricData.hotness > 2 ? 'amber' : 'gray'}
                />
              )}
              {metricData.recentPapers !== undefined && (
                <MetricsCard
                  label="Recent Papers"
                  value={metricData.recentPapers}
                  description="Papers in last 3 years"
                  color="blue"
                />
              )}
              {metricData.theoryDiversity !== undefined && (
                <MetricsCard
                  label="Theory Diversity"
                  value={metricData.theoryDiversity}
                  description="Number of distinct theories explaining this"
                  color="purple"
                />
              )}
              {metricData.evidenceStrength && (
                <MetricsCard
                  label="Avg Connection Strength"
                  value={metricData.evidenceStrength.avgConnectionStrength}
                  description="Average strength from theories"
                  color="indigo"
                />
              )}
              {supportingData?.total_papers !== undefined && (
                <MetricsCard
                  label="Total Papers"
                  value={supportingData.total_papers}
                  description={`Studied in ${supportingData.total_papers} papers`}
                  color="green"
                />
              )}
            </>
          )}
        </div>

        {/* LLM Narrative */}
        {narrative && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl shadow-lg p-6 border border-blue-100">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Intelligence Summary</h2>
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-700 leading-relaxed whitespace-pre-line">{narrative}</p>
            </div>
          </div>
        )}

        {/* Supporting Data (Collapsible) */}
        {supportingData && Object.keys(supportingData).length > 0 && (
          <details className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
            <summary className="text-lg font-semibold text-gray-900 cursor-pointer">
              Supporting Data
            </summary>
            <div className="mt-4">
              <pre className="text-xs text-gray-600 overflow-x-auto">
                {JSON.stringify(supportingData, null, 2)}
              </pre>
            </div>
          </details>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/')}
            className="mb-6 text-blue-600 hover:text-blue-700 font-semibold transition-colors"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Knowledge Metrics</h1>
          <SearchBar
            onSearch={handleSearch}
            placeholder={`Search ${entityType || 'theories'}...`}
          />
        </div>

        {/* Search Results */}
        {showSearch && searchResults.length > 0 && (
          <div className="mb-8 bg-white rounded-xl shadow-lg p-6 border border-gray-100">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Search Results ({searchResults.length})
            </h2>
            <div className="space-y-2">
              {searchResults.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleEntitySelect(item.name || item.phenomenon_name)}
                  className="w-full text-left p-4 bg-gray-50 hover:bg-blue-50 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {item.name || item.phenomenon_name}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        {item.paperCount || item.paper_count || 0} papers
                        {item.phenomenonCount !== undefined && ` • ${item.phenomenonCount} phenomena`}
                        {item.theoryCount !== undefined && ` • ${item.theoryCount} theories`}
                      </p>
                    </div>
                    <span className="text-blue-600 font-semibold">View Metrics →</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-500 text-red-700 px-4 py-3 rounded-r-lg shadow-md">
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="py-12">
            <Loading message="Loading metrics..." />
          </div>
        )}

        {/* Metrics Display */}
        {!loading && !error && renderMetrics()}

        {/* Empty State */}
        {!loading && !error && !metrics && !showSearch && (
          <div className="text-center py-16 bg-white rounded-2xl shadow-sm border border-gray-200">
            <p className="text-gray-600 mb-2 text-lg font-semibold">No metrics loaded</p>
            <p className="text-sm text-gray-500 mb-4">
              Search for a {entityType || 'theory'} to view its metrics
            </p>
            <button
              onClick={() => setShowSearch(true)}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Start Search
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MetricsDashboard;

