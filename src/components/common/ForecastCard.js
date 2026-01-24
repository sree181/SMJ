import React from 'react';

const ForecastCard = ({ forecast }) => {
  if (!forecast) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-500">
        Insufficient data for forecast
      </div>
    );
  }

  const getTrendColor = (direction) => {
    switch (direction) {
      case 'increasing':
        return 'bg-green-50 border-green-200 text-green-900';
      case 'decreasing':
        return 'bg-red-50 border-red-200 text-red-900';
      case 'stable':
        return 'bg-gray-50 border-gray-200 text-gray-900';
      default:
        return 'bg-blue-50 border-blue-200 text-blue-900';
    }
  };

  const getTrendIcon = (direction) => {
    switch (direction) {
      case 'increasing':
        return '📈';
      case 'decreasing':
        return '📉';
      case 'stable':
        return '➡️';
      default:
        return '📊';
    }
  };

  const confidenceColor = forecast.confidence >= 0.7 ? 'text-green-600' : 
                         forecast.confidence >= 0.5 ? 'text-yellow-600' : 'text-red-600';

  return (
    <div className={`rounded-lg p-6 border-2 ${getTrendColor(forecast.trend_direction)}`}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="text-2xl mb-2">{getTrendIcon(forecast.trend_direction)}</div>
          <h3 className="text-xl font-bold mb-1">Forecast: {forecast.next_period}</h3>
          <div className="text-sm opacity-80">
            {forecast.trend_direction.charAt(0).toUpperCase() + forecast.trend_direction.slice(1)} trend
          </div>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold mb-1">
            {forecast.predicted_paper_count}
          </div>
          <div className="text-sm opacity-80">papers</div>
        </div>
      </div>

      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-semibold">Confidence</span>
          <span className={`text-sm font-bold ${confidenceColor}`}>
            {(forecast.confidence * 100).toFixed(0)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${
              forecast.confidence >= 0.7 ? 'bg-green-500' :
              forecast.confidence >= 0.5 ? 'bg-yellow-500' : 'bg-red-500'
            }`}
            style={{ width: `${forecast.confidence * 100}%` }}
          />
        </div>
      </div>

      <div className="pt-4 border-t border-current border-opacity-20">
        <div className="text-sm leading-relaxed opacity-90">
          {forecast.rationale}
        </div>
      </div>
    </div>
  );
};

export default ForecastCard;


