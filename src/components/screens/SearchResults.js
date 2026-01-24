import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import SearchBar from '../common/SearchBar';
import PaperCard from '../common/PaperCard';
import Loading from '../common/Loading';
import api from '../../services/api';

const SearchResults = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const query = searchParams.get('q') || '';

  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (query) {
      performSearch(query);
    }
  }, [query]);

  const performSearch = async (searchQuery) => {
    try {
      setLoading(true);
      setError(null);

      // Check if it's a natural language question
      const isQuestion = /^(what|how|when|where|why|who|which|can|could|would|should|is|are|do|does|did|tell|show|find|list|explain|describe)\s/i.test(searchQuery.trim());
      
      if (isQuestion) {
        // For questions, use LLM query endpoint which uses Neo4j + LLM
        try {
          const ragResponse = await api.queryGraphRAG(searchQuery, null); // No persona for search results
          
          // Extract papers from sources
          if (ragResponse.sources && Array.isArray(ragResponse.sources)) {
            setResults(ragResponse.sources);
          } else {
            // If no sources, try regular search as fallback
            await performRegularSearch(searchQuery);
          }
        } catch (queryError) {
          console.error('Query endpoint failed, trying regular search:', queryError);
          // Fallback to regular search
          await performRegularSearch(searchQuery);
        }
      } else {
        // Regular search - search Neo4j directly
        await performRegularSearch(searchQuery);
      }
    } catch (err) {
      console.error('Search error:', err);
      setError(`Failed to perform search: ${err.message}`);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const performRegularSearch = async (searchQuery) => {
    try {
      const data = await api.searchPapers(searchQuery);
      if (data.papers && Array.isArray(data.papers)) {
        setResults(data.papers);
      } else if (data.papers) {
        setResults([data.papers]);
      } else {
        setResults([]);
      }
    } catch (searchError) {
      console.error('Search endpoint failed:', searchError);
      setError(`Search failed: ${searchError.message}`);
      setResults([]);
    }
  };

  const handleSearch = (newQuery) => {
    navigate(`/search?q=${encodeURIComponent(newQuery)}`);
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
        </div>

        {/* Search Query Display */}
        {query && (
          <div className="mb-6 bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <p className="text-gray-600">
              Search results for:{' '}
              <span className="font-semibold text-gray-900">"{query}"</span>
            </p>
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
            <Loading message="Searching..." />
          </div>
        )}

        {/* Results */}
        {!loading && !error && (
          <>
            <div className="mb-6 flex items-center justify-between">
              <p className="text-gray-600 font-semibold text-lg">
                {results.length} {results.length === 1 ? 'result' : 'results'} found
              </p>
            </div>

            {results.length === 0 && !loading ? (
              <div className="text-center py-16 bg-white rounded-2xl shadow-sm border border-gray-200">
                <p className="text-gray-600 mb-2 text-lg font-semibold">No results found</p>
                <p className="text-sm text-gray-500">
                  Try a different search query or browse from the dashboard
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-6">
                {results.map((paper, index) => (
                  <PaperCard key={paper.paper_id || paper.id || index} paper={paper} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default SearchResults;
