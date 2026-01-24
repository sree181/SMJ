import React from 'react';

const IntegrationSuggestions = ({ feasibility, suggestions, rationale }) => {
  const getFeasibilityColor = (feasibility) => {
    if (feasibility === 'high') return 'bg-green-100 border-green-300 text-green-800';
    if (feasibility === 'medium') return 'bg-yellow-100 border-yellow-300 text-yellow-800';
    return 'bg-red-100 border-red-300 text-red-800';
  };

  const getFeasibilityLabel = (feasibility) => {
    if (feasibility === 'high') return 'High Feasibility';
    if (feasibility === 'medium') return 'Medium Feasibility';
    return 'Low Feasibility';
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold text-gray-900">
          Integration Opportunities
        </h2>
        <span className={`px-4 py-2 rounded-lg border-2 font-semibold ${getFeasibilityColor(feasibility)}`}>
          {getFeasibilityLabel(feasibility)}
        </span>
      </div>

      {rationale && (
        <p className="text-gray-700 mb-4 italic">{rationale}</p>
      )}

      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-3">
          Suggested Integration Approaches
        </h3>
        <ul className="space-y-3">
          {suggestions.map((suggestion, idx) => (
            <li key={idx} className="flex items-start">
              <span className="text-blue-600 mr-3 mt-1">→</span>
              <span className="text-gray-700">{suggestion}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default IntegrationSuggestions;

