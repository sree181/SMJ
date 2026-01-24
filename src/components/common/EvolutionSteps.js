import React from 'react';

const EvolutionSteps = ({ evolutionSteps }) => {
  if (!evolutionSteps || evolutionSteps.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center text-gray-500">
        No evolution data available
      </div>
    );
  }

  const getEvolutionColor = (type) => {
    switch (type) {
      case 'increasing':
        return 'bg-green-100 border-green-300 text-green-800';
      case 'decreasing':
        return 'bg-red-100 border-red-300 text-red-800';
      case 'stable':
        return 'bg-gray-100 border-gray-300 text-gray-800';
      default:
        return 'bg-blue-100 border-blue-300 text-blue-800';
    }
  };

  const getEvolutionIcon = (type) => {
    switch (type) {
      case 'increasing':
        return '↑';
      case 'decreasing':
        return '↓';
      case 'stable':
        return '→';
      default:
        return '•';
    }
  };

  return (
    <div className="bg-white rounded-lg p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Evolution Between Periods</h3>
      
      <div className="space-y-3">
        {evolutionSteps.map((step, idx) => (
          <div
            key={idx}
            className={`border rounded-lg p-4 ${getEvolutionColor(step.evolution_type)}`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-2xl font-bold">{getEvolutionIcon(step.evolution_type)}</span>
                <div>
                  <div className="font-semibold">
                    {step.from_period} → {step.to_period}
                  </div>
                  <div className="text-sm opacity-80">
                    {step.evolution_type.charAt(0).toUpperCase() + step.evolution_type.slice(1)}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold">
                  {step.change > 0 ? '+' : ''}{step.change}
                </div>
                <div className="text-sm opacity-80">
                  {step.change_percentage > 0 ? '+' : ''}{step.change_percentage.toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EvolutionSteps;


