import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import Loading from '../common/Loading';
import TheoryCard from '../common/TheoryCard';
import CompatibilityVisualization from '../common/CompatibilityVisualization';
import TensionsList from '../common/TensionsList';
import IntegrationSuggestions from '../common/IntegrationSuggestions';

const TheoryComparison = () => {
  const navigate = useNavigate();
  const [theories, setTheories] = useState([]);
  const [selectedTheories, setSelectedTheories] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [userQuery, setUserQuery] = useState('');

  useEffect(() => {
    loadTheories();
  }, []);

  const loadTheories = async () => {
    try {
      const response = await api.listTheories(100, 0, 'paper_count');
      setTheories(response.theories || []);
    } catch (err) {
      console.error('Error loading theories:', err);
    }
  };

  const handleTheoryToggle = (theoryName) => {
    setSelectedTheories(prev => {
      if (prev.includes(theoryName)) {
        return prev.filter(t => t !== theoryName);
      } else if (prev.length < 5) {
        return [...prev, theoryName];
      }
      return prev;
    });
  };

  const handleCompare = async () => {
    if (selectedTheories.length < 2) {
      setError('Please select at least 2 theories to compare');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.compareTheories(selectedTheories, userQuery || null);
      setComparisonData(response);
    } catch (err) {
      console.error('Error comparing theories:', err);
      setError(err.message || 'Failed to compare theories');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setSelectedTheories([]);
    setComparisonData(null);
    setError(null);
    setUserQuery('');
  };

  const filteredTheories = theories.filter(t =>
    t.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Theory Comparison
          </h1>
          <p className="text-gray-600 text-lg">
            Compare theories to analyze compatibility, tensions, and integration opportunities
          </p>
        </div>

        {/* Theory Selection */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Select Theories to Compare
          </h2>
          
          {/* Search */}
          <div className="mb-4">
            <input
              type="text"
              placeholder="Search theories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Selected Theories */}
          {selectedTheories.length > 0 && (
            <div className="mb-4">
              <div className="flex flex-wrap gap-2">
                {selectedTheories.map((theory, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium flex items-center gap-2"
                  >
                    {theory}
                    <button
                      onClick={() => handleTheoryToggle(theory)}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Theory List */}
          <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-lg p-2 mb-4">
            {filteredTheories.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No theories found</p>
            ) : (
              <div className="space-y-1">
                {filteredTheories.map((theory) => (
                  <button
                    key={theory.name}
                    onClick={() => handleTheoryToggle(theory.name)}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                      selectedTheories.includes(theory.name)
                        ? 'bg-blue-100 text-blue-900 font-medium'
                        : 'hover:bg-gray-100 text-gray-700'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span>{theory.name}</span>
                      {theory.paperCount > 0 && (
                        <span className="text-xs text-gray-500">
                          {theory.paperCount} papers
                        </span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Optional Query */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Optional: Add context or question
            </label>
            <input
              type="text"
              placeholder="e.g., How compatible are these theories?"
              value={userQuery}
              onChange={(e) => setUserQuery(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={handleCompare}
              disabled={selectedTheories.length < 2 || loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Comparing...' : 'Compare Theories'}
            </button>
            <button
              onClick={handleClear}
              className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition-colors"
            >
              Clear
            </button>
          </div>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}
        </div>

        {/* Comparison Results */}
        {loading && <Loading />}

        {comparisonData && !loading && (
          <div className="space-y-6">
            {/* Compatibility Score */}
            <CompatibilityVisualization
              score={comparisonData.compatibility.score}
              factors={comparisonData.compatibility.factors}
            />

            {/* Theory Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {comparisonData.theories.map((theory, idx) => (
                <div key={idx} className="flex flex-col">
                  <TheoryCard
                    theory={theory}
                    phenomena={comparisonData.unique_phenomena[theory] || []}
                    sharedPhenomena={comparisonData.shared_phenomena.filter(
                      p => p.theories.includes(theory)
                    )}
                  />
                  <button
                    onClick={() => navigate(`/theories/${encodeURIComponent(theory)}`)}
                    className="mt-4 w-full px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors shadow-md hover:shadow-lg"
                  >
                    View Full Context →
                  </button>
                </div>
              ))}
            </div>

            {/* Tensions */}
            {comparisonData.tensions.length > 0 && (
              <TensionsList tensions={comparisonData.tensions} />
            )}

            {/* Integration Suggestions */}
            <IntegrationSuggestions
              feasibility={comparisonData.integration.feasibility}
              suggestions={comparisonData.integration.suggestions}
              rationale={comparisonData.integration.rationale}
            />

            {/* LLM Narrative */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                Comprehensive Analysis
              </h2>
              <div className="prose max-w-none text-gray-700 whitespace-pre-wrap">
                {comparisonData.narrative}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TheoryComparison;

