import React from 'react';

const TensionsList = ({ tensions }) => {
  const getTensionIcon = (type) => {
    if (type === 'competing_explanation') return '⚡';
    if (type === 'domain_divergence') return '↔️';
    return '⚠️';
  };

  const getTensionColor = (type) => {
    if (type === 'competing_explanation') return 'border-orange-200 bg-orange-50';
    if (type === 'domain_divergence') return 'border-yellow-200 bg-yellow-50';
    return 'border-red-200 bg-red-50';
  };

  if (tensions.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <h2 className="text-2xl font-semibold text-gray-900 mb-4">
        Identified Tensions
      </h2>
      
      <div className="space-y-4">
        {tensions.map((tension, idx) => (
          <div
            key={idx}
            className={`border-2 rounded-lg p-4 ${getTensionColor(tension.type)}`}
          >
            <div className="flex items-start">
              <span className="text-2xl mr-3">{getTensionIcon(tension.type)}</span>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 mb-1">
                  {tension.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </h3>
                <p className="text-gray-700 mb-2">{tension.description}</p>
                {tension.evidence && (
                  <p className="text-sm text-gray-600 italic">
                    Evidence: {tension.evidence}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TensionsList;

