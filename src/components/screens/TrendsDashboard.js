import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import TrendChart from '../common/TrendChart';
import EvolutionSteps from '../common/EvolutionSteps';
import ForecastCard from '../common/ForecastCard';
import Loading from '../common/Loading';
import api from '../../services/api';

const TrendsDashboard = () => {
  const navigate = useNavigate();
  const { entityType, entityName } = useParams();
  const [trendData, setTrendData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (entityType && entityName) {
      loadTrendData();
    }
  }, [entityType, entityName]);

  const loadTrendData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const decodedName = decodeURIComponent(entityName);
      const data = await api.getTrendAnalysis(entityType, decodedName);
      setTrendData(data);
    } catch (err) {
      console.error('Error loading trend data:', err);
      setError(`Failed to load trend analysis: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loading />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="text-red-800">{error}</div>
            <button
              onClick={() => navigate('/')}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!trendData) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-lg p-6 text-center">
            <div className="text-gray-500">No trend data available</div>
            <button
              onClick={() => navigate('/')}
              className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
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
            Trend Analysis: {trendData.entity_name}
          </h1>
          <p className="text-lg text-gray-600 capitalize">
            {trendData.entity_type} • Temporal Evolution
          </p>
        </div>

        {/* Summary */}
        {trendData.summary && (
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold text-indigo-900 mb-2">Summary</h2>
            <div className="text-indigo-800 leading-relaxed">
              {trendData.summary}
            </div>
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Trend Chart */}
          <div className="lg:col-span-2">
            <TrendChart
              usageByPeriod={trendData.usage_by_period}
              forecast={trendData.forecast}
            />
          </div>

          {/* Evolution Steps */}
          <div>
            <EvolutionSteps evolutionSteps={trendData.evolution_steps} />
          </div>

          {/* Forecast */}
          <div>
            <ForecastCard forecast={trendData.forecast} />
          </div>
        </div>

        {/* Narrative */}
        {trendData.narrative && (
          <div className="bg-white rounded-lg p-6 border border-gray-200 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Detailed Analysis</h2>
            <div className="text-gray-700 leading-relaxed whitespace-pre-line">
              {trendData.narrative}
            </div>
          </div>
        )}

        {/* Usage Details Table */}
        {trendData.usage_by_period && trendData.usage_by_period.length > 0 && (
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Usage by Period</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Period
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Years
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Papers
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Frequency
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {trendData.usage_by_period.map((period, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {period.period}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {period.start_year} - {period.end_year}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {period.paper_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {period.usage_frequency ? period.usage_frequency.toFixed(2) : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TrendsDashboard;


