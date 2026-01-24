import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import SearchBar from '../common/SearchBar';
import PersonaSelector from '../common/PersonaSelector';
import PaperCard from '../common/PaperCard';
import Loading from '../common/Loading';
import api from '../../services/api';

const QueryResults = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const query = searchParams.get('q') || '';
  const personaParam = searchParams.get('persona') || null;

  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedPersona, setSelectedPersona] = useState(personaParam);

  useEffect(() => {
    if (query) {
      performQuery(query, selectedPersona);
    }
  }, [query, selectedPersona]);

  const performQuery = async (queryText, persona = null) => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.queryGraphRAG(queryText, persona);
      
      if (response.answer) {
        setAnswer(response.answer);
      }
      
      if (response.sources && Array.isArray(response.sources)) {
        setSources(response.sources);
      }
    } catch (err) {
      console.error('Query error:', err);
      setError(`Failed to process query: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (newQuery) => {
    const params = new URLSearchParams({ q: newQuery });
    if (selectedPersona) {
      params.set('persona', selectedPersona);
    }
    navigate(`/query?${params.toString()}`);
  };

  const handlePersonaChange = (persona) => {
    setSelectedPersona(persona);
    // Update URL without triggering new query (query will be triggered by useEffect)
    const params = new URLSearchParams({ q: query });
    if (persona) {
      params.set('persona', persona);
    }
    navigate(`/query?${params.toString()}`, { replace: true });
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
          <SearchBar onSearch={handleSearch} />
          
          {/* Persona Selector */}
          <div className="mt-6">
            <PersonaSelector
              selectedPersona={selectedPersona}
              onPersonaChange={handlePersonaChange}
            />
          </div>
        </div>

        {/* Query Display */}
        {query && (
          <div className="mb-6 bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <p className="text-gray-600">
                Query: <span className="font-semibold text-gray-900">"{query}"</span>
              </p>
              {selectedPersona && (
                <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold">
                  {selectedPersona === 'historian' && '📜 Historian'}
                  {selectedPersona === 'reviewer2' && '🔍 Reviewer #2'}
                  {selectedPersona === 'advisor' && '💡 Advisor'}
                  {selectedPersona === 'strategist' && '🎯 Strategist'}
                </span>
              )}
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
            <Loading message="Processing query with LLM..." />
          </div>
        )}

        {/* Answer */}
        {!loading && !error && answer && (
          <div className="mb-8 bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Answer</h2>
            <div className="prose max-w-none">
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{answer}</p>
            </div>
          </div>
        )}

        {/* Sources */}
        {!loading && !error && sources.length > 0 && (
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-4">
              Related Papers ({sources.length})
            </h3>
            <div className="grid grid-cols-1 gap-6">
              {sources.map((source, index) => (
                <PaperCard key={source.paper_id || source.id || index} paper={source} />
              ))}
            </div>
          </div>
        )}

        {!loading && !error && !answer && !sources.length && (
          <div className="text-center py-16 bg-white rounded-2xl shadow-sm border border-gray-200">
            <p className="text-gray-600 mb-2 text-lg font-semibold">No results found</p>
            <p className="text-sm text-gray-500">
              Try rephrasing your question or use a different search query
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default QueryResults;

