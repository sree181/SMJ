import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../common/SearchBar';
import StatsCard from '../common/StatsCard';
import Loading from '../common/Loading';
import api from '../../services/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    papers: 0,
    theories: 0,
    methods: 0,
    authors: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await api.getStats();
      
      // Handle both old and new API response formats
      setStats({
        papers: data.papers || 0,
        theories: data.theories || data.entities || 0,
        methods: data.methods || data.methodologies || 0,
        authors: data.authors || 0,
      });
      setError(null);
    } catch (err) {
      console.error('Error loading stats:', err);
      setError(`Failed to load statistics: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (query) => {
    navigate(`/search?q=${encodeURIComponent(query)}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loading message="Loading dashboard..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="relative bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-600 text-white">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative max-w-7xl mx-auto px-4 py-16 sm:py-24">
          <div className="text-center">
            <h1 className="text-5xl sm:text-6xl font-bold mb-4 tracking-tight">
              Research Assistant
            </h1>
            <p className="text-xl sm:text-2xl text-blue-100 mb-8 max-w-2xl mx-auto">
              Explore Strategic Management Journal Research
            </p>
            
            {/* Search Bar */}
            <div className="mt-10">
              <SearchBar onSearch={handleSearch} />
            </div>
          </div>
        </div>
        
        {/* Wave separator */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M0 120L60 105C120 90 240 60 360 45C480 30 600 30 720 37.5C840 45 960 60 1080 67.5C1200 75 1320 75 1380 75L1440 75V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z" fill="#f8fafc"/>
          </svg>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-12 -mt-8 relative z-10">
        {/* Error Message */}
        {error && (
          <div className="mb-8 bg-red-50 border-l-4 border-red-500 text-red-700 px-4 py-3 rounded-r-lg shadow-md">
            {error}
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <StatsCard
            label="Papers"
            value={stats.papers}
            color="blue"
            onClick={() => handleSearch('papers')}
          />
          <StatsCard
            label="Theories"
            value={stats.theories}
            color="purple"
            onClick={() => handleSearch('theories')}
          />
          <StatsCard
            label="Methods"
            value={stats.methods}
            color="green"
            onClick={() => handleSearch('methods')}
          />
          <StatsCard
            label="Authors"
            value={stats.authors}
            color="amber"
            onClick={() => handleSearch('authors')}
          />
        </div>

        {/* Feature Cards */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Explore Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div
              onClick={() => navigate('/theories/compare')}
              className="group bg-white rounded-2xl shadow-lg p-8 hover:shadow-2xl transition-all duration-300 cursor-pointer border border-gray-100 hover:border-indigo-200 transform hover:-translate-y-2"
            >
              <div className="h-2 bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-t-2xl -mx-8 -mt-8 mb-6"></div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">Theory Comparison</h3>
              <p className="text-gray-600 leading-relaxed mb-4">
                Compare theories to analyze compatibility, tensions, and integration opportunities. View full context for any theory.
              </p>
              <div className="text-indigo-600 font-semibold group-hover:text-indigo-700">
                Compare Theories →
              </div>
            </div>

            <div
              onClick={() => navigate('/search')}
              className="group bg-white rounded-2xl shadow-lg p-8 hover:shadow-2xl transition-all duration-300 cursor-pointer border border-gray-100 hover:border-blue-200 transform hover:-translate-y-2"
            >
              <div className="h-2 bg-gradient-to-r from-blue-500 to-blue-600 rounded-t-2xl -mx-8 -mt-8 mb-6"></div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">Trend Analysis</h3>
              <p className="text-gray-600 leading-relaxed mb-4">
                Analyze temporal trends for theories, methods, and phenomena. View usage patterns, evolution steps, and forecasts for future periods.
              </p>
              <div className="text-blue-600 font-semibold group-hover:text-blue-700">
                Search for entity →
              </div>
            </div>

            <div
              onClick={() => navigate('/graph')}
              className="group bg-white rounded-2xl shadow-lg p-8 hover:shadow-2xl transition-all duration-300 cursor-pointer border border-gray-100 hover:border-purple-200 transform hover:-translate-y-2"
            >
              <div className="h-2 bg-gradient-to-r from-purple-500 to-purple-600 rounded-t-2xl -mx-8 -mt-8 mb-6"></div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">Graph Explorer</h3>
              <p className="text-gray-600 leading-relaxed mb-4">
                Visualize connections between papers, theories, methods, and authors. Explore the knowledge graph interactively to discover relationships.
              </p>
              <div className="text-purple-600 font-semibold group-hover:text-purple-700">
                Explore →
              </div>
            </div>

            <div
              onClick={() => navigate('/analytics')}
              className="group bg-white rounded-2xl shadow-lg p-8 hover:shadow-2xl transition-all duration-300 cursor-pointer border border-gray-100 hover:border-emerald-200 transform hover:-translate-y-2"
            >
              <div className="h-2 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-t-2xl -mx-8 -mt-8 mb-6"></div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">Advanced Analytics Dashboard</h3>
              <p className="text-gray-600 leading-relaxed mb-4">
                Sophisticated metrics powered by Graph RAG: Paper counts by 5-year intervals, topic evolution, and theoretical divergence analysis (1985-2025).
              </p>
              <div className="text-emerald-600 font-semibold group-hover:text-emerald-700">
                Explore →
              </div>
            </div>

            <div
              onClick={() => navigate('/query')}
              className="group bg-white rounded-2xl shadow-lg p-8 hover:shadow-2xl transition-all duration-300 cursor-pointer border border-gray-100 hover:border-amber-200 transform hover:-translate-y-2"
            >
              <div className="h-2 bg-gradient-to-r from-amber-500 to-amber-600 rounded-t-2xl -mx-8 -mt-8 mb-6"></div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">Query Interface</h3>
              <p className="text-gray-600 leading-relaxed mb-4">
                Ask natural language questions about the research. Get intelligent answers powered by the knowledge graph and LLM.
              </p>
              <div className="text-amber-600 font-semibold group-hover:text-amber-700">
                Explore →
              </div>
            </div>

            <div
              onClick={() => navigate('/contributions/opportunities')}
              className="group bg-white rounded-2xl shadow-lg p-8 hover:shadow-2xl transition-all duration-300 cursor-pointer border border-gray-100 hover:border-teal-200 transform hover:-translate-y-2"
            >
              <div className="h-2 bg-gradient-to-r from-teal-500 to-teal-600 rounded-t-2xl -mx-8 -mt-8 mb-6"></div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">Contribution Opportunities</h3>
              <p className="text-gray-600 leading-relaxed mb-4">
                Discover underexplored research gaps, theory-phenomenon combinations, and rare constructs. Get contribution statements and research questions.
              </p>
              <div className="text-teal-600 font-semibold group-hover:text-teal-700">
                Explore →
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
