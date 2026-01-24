import React from 'react';

const TrendChart = ({ usageByPeriod, forecast }) => {
  if (!usageByPeriod || usageByPeriod.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
        No temporal data available
      </div>
    );
  }

  // Calculate max value for scaling
  const allValues = usageByPeriod.map(p => p.paper_count);
  if (forecast) {
    allValues.push(forecast.predicted_paper_count);
  }
  const maxValue = Math.max(...allValues, 1);
  const chartHeight = 300;
  const barWidth = 60;
  const spacing = 20;

  return (
    <div className="bg-white rounded-lg p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Usage Over Time</h3>
      
      <div className="relative" style={{ height: `${chartHeight + 60}px` }}>
        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 bottom-12 flex flex-col justify-between text-xs text-gray-600">
          {[0, Math.ceil(maxValue * 0.5), maxValue].map((value, idx) => (
            <span key={idx}>{value}</span>
          ))}
        </div>

        {/* Chart area */}
        <div className="ml-12 relative" style={{ height: `${chartHeight}px` }}>
          {/* Grid lines */}
          <div className="absolute inset-0 flex flex-col justify-between">
            {[0, 0.5, 1].map((ratio) => (
              <div
                key={ratio}
                className="border-t border-gray-200"
                style={{ marginTop: `${ratio * chartHeight}px` }}
              />
            ))}
          </div>

          {/* Bars */}
          <div className="absolute inset-0 flex items-end gap-4">
            {usageByPeriod.map((period, idx) => {
              const height = (period.paper_count / maxValue) * chartHeight;
              return (
                <div key={idx} className="flex flex-col items-center flex-1">
                  <div
                    className="bg-indigo-500 rounded-t hover:bg-indigo-600 transition-colors w-full"
                    style={{ height: `${height}px` }}
                    title={`${period.period}: ${period.paper_count} papers`}
                  />
                  <div className="mt-2 text-xs text-gray-600 text-center">
                    <div className="font-semibold">{period.paper_count}</div>
                    <div className="text-gray-500">{period.period}</div>
                  </div>
                </div>
              );
            })}
            
            {/* Forecast bar */}
            {forecast && (
              <div className="flex flex-col items-center flex-1">
                <div
                  className="bg-teal-500 rounded-t hover:bg-teal-600 transition-colors w-full border-2 border-dashed border-teal-700"
                  style={{ height: `${(forecast.predicted_paper_count / maxValue) * chartHeight}px` }}
                  title={`${forecast.next_period} (forecast): ${forecast.predicted_paper_count} papers`}
                />
                <div className="mt-2 text-xs text-gray-600 text-center">
                  <div className="font-semibold text-teal-700">{forecast.predicted_paper_count}</div>
                  <div className="text-gray-500 italic">{forecast.next_period}</div>
                  <div className="text-xs text-teal-600">(forecast)</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-indigo-500 rounded"></div>
          <span className="text-gray-600">Historical</span>
        </div>
        {forecast && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-teal-500 rounded border-2 border-dashed border-teal-700"></div>
            <span className="text-gray-600">Forecast</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default TrendChart;


