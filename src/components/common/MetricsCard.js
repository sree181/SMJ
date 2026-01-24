import React from 'react';

/**
 * MetricsCard Component
 * Displays a single metric with label, value, and optional trend indicator
 */
const MetricsCard = ({ label, value, unit = '', trend = null, description = '', color = 'blue' }) => {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    purple: 'from-purple-500 to-purple-600',
    green: 'from-green-500 to-green-600',
    amber: 'from-amber-500 to-amber-600',
    red: 'from-red-500 to-red-600',
    indigo: 'from-indigo-500 to-indigo-600'
  };

  const bgColor = colorClasses[color] || colorClasses.blue;

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">
            {label}
          </h3>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-bold text-gray-900">
              {typeof value === 'number' ? value.toFixed(value < 1 ? 3 : value < 10 ? 2 : 0) : value}
            </span>
            {unit && (
              <span className="text-lg text-gray-500">{unit}</span>
            )}
          </div>
        </div>
        {trend !== null && (
          <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
            trend > 0 
              ? 'bg-green-100 text-green-700' 
              : trend < 0 
              ? 'bg-red-100 text-red-700' 
              : 'bg-gray-100 text-gray-700'
          }`}>
            {trend > 0 ? '↑' : trend < 0 ? '↓' : '→'} {Math.abs(trend).toFixed(1)}%
          </div>
        )}
      </div>
      {description && (
        <p className="text-sm text-gray-500 mt-2">{description}</p>
      )}
      {typeof value === 'number' && value >= 0 && value <= 1 && (
        <div className="mt-3">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`bg-gradient-to-r ${bgColor} h-2 rounded-full transition-all duration-500`}
              style={{ width: `${value * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default MetricsCard;

