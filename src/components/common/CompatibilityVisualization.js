import React from 'react';

const CompatibilityVisualization = ({ score, factors }) => {
  const getScoreColor = (score) => {
    if (score >= 0.7) return 'bg-green-500';
    if (score >= 0.4) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getScoreLabel = (score) => {
    if (score >= 0.7) return 'High Compatibility';
    if (score >= 0.4) return 'Moderate Compatibility';
    return 'Low Compatibility';
  };

  const percentage = Math.round(score * 100);

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <h2 className="text-2xl font-semibold text-gray-900 mb-4">
        Compatibility Analysis
      </h2>
      
      {/* Score Display */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-lg font-medium text-gray-700">
            {getScoreLabel(score)}
          </span>
          <span className="text-3xl font-bold text-gray-900">
            {score.toFixed(2)}
          </span>
        </div>
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
          <div
            className={`h-full ${getScoreColor(score)} transition-all duration-500`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <div className="text-sm text-gray-500 mt-1">
          {percentage}% compatible
        </div>
      </div>

      {/* Factors */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">
          Compatibility Factors
        </h3>
        <ul className="space-y-2">
          {factors.map((factor, idx) => (
            <li key={idx} className="flex items-start">
              <span className="text-blue-600 mr-2">•</span>
              <span className="text-gray-700">{factor}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default CompatibilityVisualization;

