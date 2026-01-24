import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import OpportunityCard from '../common/OpportunityCard';
import Loading from '../common/Loading';
import api from '../../services/api';

const ContributionExplorer = () => {
  const navigate = useNavigate();
  const [opportunities, setOpportunities] = useState([]);
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filters
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [minPotential, setMinPotential] = useState(0.5);
  const [limit, setLimit] = useState(20);

  useEffect(() => {
    loadOpportunities();
  }, [typeFilter, minPotential, limit]);

  const loadOpportunities = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const filters = {
        query: query || undefined,
        type: typeFilter !== 'all' ? typeFilter : undefined,
        min_potential: minPotential,
        limit: limit,
      };
      
      const data = await api.getContributionOpportunities(filters);
      setOpportunities(data.opportunities || []);
      setSummary(data.summary || '');
    } catch (err) {
      console.error('Error loading opportunities:', err);
      setError(`Failed to load opportunities: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadOpportunities();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  if (loading && opportunities.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loading />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-900 mb-4 text-sm"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Contribution Opportunities
          </h1>
          <p className="text-lg text-gray-600">
            Discover underexplored research gaps and contribution opportunities
          </p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search Query */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Search
              </label>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Search opportunities..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            {/* Type Filter */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Type
              </label>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="all">All Types</option>
                <option value="theory-phenomenon">Theory-Phenomenon</option>
                <option value="theory-method">Theory-Method</option>
                <option value="construct">Rare Constructs</option>
              </select>
            </div>

            {/* Min Potential */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Min Score: {(minPotential * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={minPotential}
                onChange={(e) => setMinPotential(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Limit */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Limit
              </label>
              <select
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="10">10</option>
                <option value="20">20</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleSearch}
            className="mt-4 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-semibold"
          >
            Search
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="text-red-800">{error}</div>
          </div>
        )}

        {/* Summary */}
        {summary && (
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold text-indigo-900 mb-2">Summary</h2>
            <div className="text-indigo-800 leading-relaxed whitespace-pre-line">
              {summary}
            </div>
          </div>
        )}

        {/* Results Count */}
        <div className="mb-4">
          <div className="text-gray-600">
            Found <span className="font-semibold text-gray-900">{opportunities.length}</span> opportunities
          </div>
        </div>

        {/* Opportunities List */}
        {opportunities.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <div className="text-gray-500 text-lg">
              No opportunities found matching your criteria.
            </div>
            <div className="text-gray-400 text-sm mt-2">
              Try adjusting your filters or search query.
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {opportunities.map((opp, idx) => (
              <OpportunityCard key={idx} opportunity={opp} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ContributionExplorer;

