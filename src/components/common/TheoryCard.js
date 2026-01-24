import React from 'react';

const TheoryCard = ({ theory, phenomena, sharedPhenomena }) => {
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <h3 className="text-2xl font-semibold text-gray-900 mb-4">{theory}</h3>
      
      {/* Shared Phenomena */}
      {sharedPhenomena.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            Shared Phenomena ({sharedPhenomena.length})
          </h4>
          <div className="space-y-1">
            {sharedPhenomena.slice(0, 5).map((phen, idx) => (
              <div key={idx} className="text-sm text-gray-600">
                • {phen.phenomenon_name}
                {phen.avg_connection_strength && (
                  <span className="ml-2 text-xs text-gray-500">
                    (strength: {phen.avg_connection_strength.toFixed(2)})
                  </span>
                )}
              </div>
            ))}
            {sharedPhenomena.length > 5 && (
              <div className="text-xs text-gray-500">
                +{sharedPhenomena.length - 5} more
              </div>
            )}
          </div>
        </div>
      )}

      {/* Unique Phenomena */}
      {phenomena.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            Unique Phenomena ({phenomena.length})
          </h4>
          <div className="space-y-1">
            {phenomena.slice(0, 5).map((phen, idx) => (
              <div key={idx} className="text-sm text-gray-600">
                • {phen.phenomenon_name}
                {phen.connection_strength && (
                  <span className="ml-2 text-xs text-gray-500">
                    (strength: {phen.connection_strength.toFixed(2)})
                  </span>
                )}
              </div>
            ))}
            {phenomena.length > 5 && (
              <div className="text-xs text-gray-500">
                +{phenomena.length - 5} more
              </div>
            )}
          </div>
        </div>
      )}

      {phenomena.length === 0 && sharedPhenomena.length === 0 && (
        <p className="text-sm text-gray-500">No phenomena data available</p>
      )}
    </div>
  );
};

export default TheoryCard;

