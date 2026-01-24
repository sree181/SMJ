import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';
import Loading from '../common/Loading';

const TheoryDetail = () => {
  const { theoryName } = useParams();
  const navigate = useNavigate();
  const [context, setContext] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (theoryName) {
      loadTheoryContext();
    }
  }, [theoryName]);

  const loadTheoryContext = async () => {
    try {
      setLoading(true);
      setError(null);
      const decodedName = decodeURIComponent(theoryName);
      const data = await api.getTheoryContext(decodedName);
      setContext(data);
    } catch (err) {
      console.error('Error loading theory context:', err);
      setError(err.message || 'Failed to load theory context');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <Loading />;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <div className="flex gap-3">
            <button
              onClick={() => navigate('/theories/compare')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Back to Theory Comparison
            </button>
            <button
              onClick={() => navigate(`/trends/theory/${encodeURIComponent(decodedName)}`)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              View Trends
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!context) {
    return null;
  }

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'phenomena', label: 'Phenomena' },
    { id: 'methods', label: 'Methods' },
    { id: 'papers', label: 'Papers' },
    { id: 'temporal', label: 'Temporal Usage' },
    { id: 'assumptions', label: 'Assumptions' },
    { id: 'constructs', label: 'Constructs' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/theories/compare')}
            className="text-blue-600 hover:text-blue-800 mb-4"
          >
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/theories/compare')}
                className="text-gray-600 hover:text-gray-900"
              >
                ← Back to Theory Comparison
              </button>
              <button
                onClick={() => navigate(`/trends/theory/${encodeURIComponent(decodedName)}`)}
                className="px-3 py-1 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm"
              >
                View Trends
              </button>
            </div>
          </button>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            {context.theory.name}
          </h1>
          {context.theory.domain && (
            <p className="text-gray-600 text-lg">Domain: {context.theory.domain}</p>
          )}
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-2xl shadow-lg mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Phenomena</div>
                  <div className="text-2xl font-bold text-gray-900">
                    {context.phenomena.length}
                  </div>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Methods</div>
                  <div className="text-2xl font-bold text-gray-900">
                    {context.methods.length}
                  </div>
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Papers</div>
                  <div className="text-2xl font-bold text-gray-900">
                    {context.papers.length}
                  </div>
                </div>
              </div>

              {context.co_usage_theories.length > 0 && (
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-3">
                    Frequently Co-Used Theories
                  </h3>
                  <div className="space-y-2">
                    {context.co_usage_theories.map((coTheory, idx) => (
                      <div key={idx} className="border border-gray-200 rounded-lg p-3">
                        <div className="font-medium text-gray-900">
                          {coTheory.theory_name}
                        </div>
                        <div className="text-sm text-gray-600">
                          Co-used in {coTheory.co_usage_count} papers
                        </div>
                        {coTheory.shared_phenomena.length > 0 && (
                          <div className="text-xs text-gray-500 mt-1">
                            Shared phenomena: {coTheory.shared_phenomena.join(', ')}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'phenomena' && (
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Phenomena Explained ({context.phenomena.length})
              </h3>
              {context.phenomena.length === 0 ? (
                <p className="text-gray-500">No phenomena data available</p>
              ) : (
                <div className="space-y-3">
                  {context.phenomena.map((phen, idx) => (
                    <div key={idx} className="border border-gray-200 rounded-lg p-4">
                      <div className="font-medium text-gray-900 mb-1">
                        {phen.phenomenon_name}
                      </div>
                      <div className="flex gap-4 text-sm text-gray-600">
                        {phen.phenomenon_type && (
                          <span>Type: {phen.phenomenon_type}</span>
                        )}
                        {phen.domain && <span>Domain: {phen.domain}</span>}
                        <span>
                          Strength: {phen.connection_strength.toFixed(2)}
                        </span>
                        <span>Papers: {phen.paper_count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'methods' && (
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Methods Used ({context.methods.length})
              </h3>
              {context.methods.length === 0 ? (
                <p className="text-gray-500">No methods data available</p>
              ) : (
                <div className="space-y-3">
                  {context.methods.map((method, idx) => (
                    <div key={idx} className="border border-gray-200 rounded-lg p-4">
                      <div className="font-medium text-gray-900 mb-1">
                        {method.name}
                      </div>
                      <div className="flex gap-4 text-sm text-gray-600">
                        {method.category && <span>Category: {method.category}</span>}
                        <span>Used in {method.paper_count} papers</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'papers' && (
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Papers Using This Theory ({context.papers.length})
              </h3>
              {context.papers.length === 0 ? (
                <p className="text-gray-500">No papers data available</p>
              ) : (
                <div className="space-y-3">
                  {context.papers.map((paper, idx) => (
                    <div
                      key={idx}
                      className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
                      onClick={() => navigate(`/paper/${paper.paper_id}`)}
                    >
                      <div className="font-medium text-gray-900 mb-1">
                        {paper.title}
                      </div>
                      <div className="flex gap-4 text-sm text-gray-600">
                        {paper.publication_year && (
                          <span>Year: {paper.publication_year}</span>
                        )}
                        {paper.journal && <span>Journal: {paper.journal}</span>}
                      </div>
                      {paper.authors && paper.authors.length > 0 && (
                        <div className="text-xs text-gray-500 mt-1">
                          {paper.authors.slice(0, 3).join(', ')}
                          {paper.authors.length > 3 && ' et al.'}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'temporal' && (
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Temporal Usage Patterns
              </h3>
              {context.temporal_usage.length === 0 ? (
                <p className="text-gray-500">No temporal data available</p>
              ) : (
                <div>
                  <div className="mb-4">
                    <div className="flex items-end gap-2 h-64 border-b-2 border-gray-300">
                      {context.temporal_usage.map((usage, idx) => {
                        const maxCount = Math.max(...context.temporal_usage.map(u => u.paper_count));
                        const height = (usage.paper_count / maxCount) * 100;
                        return (
                          <div key={idx} className="flex-1 flex flex-col items-center">
                            <div
                              className="w-full bg-blue-500 rounded-t transition-all"
                              style={{ height: `${height}%` }}
                              title={`${usage.year}: ${usage.paper_count} papers`}
                            />
                            <div className="text-xs text-gray-600 mt-2 transform -rotate-45 origin-top-left whitespace-nowrap">
                              {usage.year}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                  <div className="space-y-2">
                    {context.temporal_usage.map((usage, idx) => (
                      <div key={idx} className="border border-gray-200 rounded-lg p-3">
                        <div className="font-medium text-gray-900">
                          {usage.year}: {usage.paper_count} papers
                        </div>
                        {usage.methods.length > 0 && (
                          <div className="text-sm text-gray-600 mt-1">
                            Methods: {usage.methods.join(', ')}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'assumptions' && (
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Assumptions Analysis
              </h3>
              <div className="prose max-w-none text-gray-700 whitespace-pre-wrap">
                {context.assumptions_narrative}
              </div>
            </div>
          )}

          {activeTab === 'constructs' && (
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Constructs Analysis
              </h3>
              {context.constructs.length > 0 && (
                <div className="mb-6 space-y-3">
                  {context.constructs.map((construct, idx) => (
                    <div key={idx} className="border border-gray-200 rounded-lg p-4">
                      <div className="font-medium text-gray-900 mb-1">
                        {construct.construct_name}
                      </div>
                      <div className="text-sm text-gray-600 mb-2">
                        Related to {construct.frequency} phenomena
                      </div>
                      {construct.related_phenomena.length > 0 && (
                        <div className="text-xs text-gray-500">
                          Phenomena: {construct.related_phenomena.join(', ')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
              <div className="prose max-w-none text-gray-700 whitespace-pre-wrap">
                {context.constructs_narrative}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TheoryDetail;

