import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Loading from '../common/Loading';
import api from '../../services/api';

const PaperDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [paper, setPaper] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadPaper();
  }, [id]);

  const loadPaper = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getPaper(id);
      setPaper(data);
    } catch (err) {
      console.error('Error loading paper:', err);
      setError('Failed to load paper details');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-50 to-white">
        <Loading message="Loading paper details..." />
      </div>
    );
  }

  if (error || !paper) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center">
        <div className="text-center bg-white rounded-2xl shadow-lg p-8 max-w-md">
          <p className="text-red-600 mb-4 text-lg font-semibold">{error || 'Paper not found'}</p>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all font-semibold shadow-md hover:shadow-lg"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const authors = paper.authors || [];
  const theories = paper.theories || [];
  const methods = paper.methods || [];
  const researchQuestions = paper.research_questions || [];

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Back Button */}
        <button
          onClick={() => navigate(-1)}
          className="mb-6 text-blue-600 hover:text-blue-700 font-semibold transition-colors"
        >
          ← Back to Results
        </button>

        {/* Paper Header Card */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 mb-6 overflow-hidden">
          <div className="h-2 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 -mx-8 -mt-8 mb-6"></div>
          
          <h1 className="text-3xl font-bold text-gray-900 mb-4 leading-tight">
            {paper.title || 'Untitled Paper'}
          </h1>

          <div className="flex flex-wrap items-center gap-4 mb-6">
            {paper.publication_year && (
              <span className="px-4 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm font-semibold border border-blue-100">
                {paper.publication_year}
              </span>
            )}
            {paper.journal && (
              <span className="text-gray-600 font-semibold">
                {paper.journal}
              </span>
            )}
          </div>

          {authors.length > 0 && (
            <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-200">
              <div className="mb-2">
                <span className="font-semibold text-gray-700">Authors</span>
              </div>
              <p className="text-gray-700">
                {authors.map((author, i) => (
                  <span key={i}>
                    {typeof author === 'string' ? author : author.full_name || author.name}
                    {i < authors.length - 1 && ', '}
                  </span>
                ))}
              </p>
            </div>
          )}

          {paper.doi && (
            <div className="text-sm text-gray-600">
              <span className="font-semibold">DOI:</span> {paper.doi}
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 mb-6 overflow-hidden">
          <div className="border-b border-gray-200 bg-gray-50">
            <nav className="flex -mb-px">
              {['overview', 'theories', 'methods', 'questions'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-6 py-4 text-sm font-semibold border-b-2 transition-colors ${
                    activeTab === tab
                      ? 'border-blue-600 text-blue-600 bg-white'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-8">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {paper.abstract && (
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-3">Abstract</h3>
                    <p className="text-gray-700 leading-relaxed text-base">{paper.abstract}</p>
                  </div>
                )}

                {paper.keywords && paper.keywords.length > 0 && (
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-3">Keywords</h3>
                    <div className="flex flex-wrap gap-2">
                      {paper.keywords.map((keyword, i) => (
                        <span
                          key={i}
                          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium border border-gray-200 hover:bg-gray-200 transition-colors"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Theories Tab */}
            {activeTab === 'theories' && (
              <div>
                {theories.length > 0 ? (
                  <div className="space-y-4">
                    {theories.map((theory, i) => {
                      if (!theory) return null;
                      const theoryName = typeof theory === 'string' 
                        ? theory 
                        : (theory.name || theory.theory_name || '');
                      if (!theoryName) return null;
                      
                      return (
                        <div key={i} className="border-l-4 border-blue-500 pl-6 py-4 bg-blue-50/50 rounded-r-xl">
                          <h4 className="font-bold text-gray-900 text-lg mb-2">
                            {theoryName}
                          </h4>
                          {typeof theory === 'object' && theory.role && (
                            <span className="inline-block px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-xs font-semibold mb-2">
                              {String(theory.role).charAt(0).toUpperCase() + String(theory.role).slice(1)}
                            </span>
                          )}
                          {typeof theory === 'object' && theory.section && (
                            <span className="inline-block px-3 py-1 bg-gray-100 text-gray-700 rounded-lg text-xs font-semibold mb-2 ml-2">
                              {String(theory.section)}
                            </span>
                          )}
                          {typeof theory === 'object' && theory.description && (
                            <p className="text-gray-700 mt-2 leading-relaxed">{String(theory.description)}</p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-gray-600">No theories found for this paper.</p>
                  </div>
                )}
              </div>
            )}

            {/* Methods Tab */}
            {activeTab === 'methods' && (
              <div>
                {methods.length > 0 ? (
                  <div className="space-y-4">
                    {methods.map((method, i) => {
                      if (!method) return null;
                      const methodName = typeof method === 'string' 
                        ? method 
                        : (method.name || method.method_name || '');
                      if (!methodName) return null;
                      
                      return (
                        <div key={i} className="border-l-4 border-emerald-500 pl-6 py-4 bg-emerald-50/50 rounded-r-xl">
                          <h4 className="font-bold text-gray-900 text-lg mb-2">
                            {methodName}
                          </h4>
                          {typeof method === 'object' && method.category && (
                            <span className="inline-block px-3 py-1 bg-emerald-100 text-emerald-700 rounded-lg text-xs font-semibold mb-2">
                              {String(method.category)}
                            </span>
                          )}
                          {typeof method === 'object' && method.description && (
                            <p className="text-gray-700 mt-2 leading-relaxed">{String(method.description)}</p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-gray-600">No methods found for this paper.</p>
                  </div>
                )}
              </div>
            )}

            {/* Questions Tab */}
            {activeTab === 'questions' && (
              <div>
                {researchQuestions.length > 0 ? (
                  <div className="space-y-4">
                    {researchQuestions.map((rq, i) => (
                      <div key={i} className="border-l-4 border-amber-500 pl-6 py-4 bg-amber-50/50 rounded-r-xl">
                        <div className="flex items-start gap-3">
                          <span className="flex-shrink-0 w-8 h-8 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center font-bold text-sm">
                            {i + 1}
                          </span>
                          <h4 className="font-semibold text-gray-900 text-base leading-relaxed">
                            {typeof rq === 'string' ? rq : rq.question || rq.text}
                          </h4>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-gray-600">No research questions found for this paper.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-4">
          <button
            onClick={() => navigate(`/graph?paper=${id}`)}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all font-semibold shadow-md hover:shadow-lg transform hover:scale-105 active:scale-100"
          >
            View in Graph
          </button>
          <button
            onClick={() => navigate(`/temporal?paper=${id}`)}
            className="px-6 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl hover:from-emerald-700 hover:to-teal-700 transition-all font-semibold shadow-md hover:shadow-lg transform hover:scale-105 active:scale-100"
          >
            Temporal Analysis
          </button>
        </div>
      </div>
    </div>
  );
};

export default PaperDetail;
