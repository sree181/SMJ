import React from 'react';

const OpportunityCard = ({ opportunity }) => {
  const getTypeColor = (type) => {
    switch (type) {
      case 'theory-phenomenon':
        return 'bg-blue-50 border-blue-200';
      case 'theory-method':
        return 'bg-purple-50 border-purple-200';
      case 'construct':
        return 'bg-green-50 border-green-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getTypeLabel = (type) => {
    switch (type) {
      case 'theory-phenomenon':
        return 'Theory-Phenomenon Gap';
      case 'theory-method':
        return 'Theory-Method Gap';
      case 'construct':
        return 'Rare Construct';
      default:
        return 'Opportunity';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-blue-600';
    if (score >= 0.5) return 'text-yellow-600';
    return 'text-gray-600';
  };

  return (
    <div className={`border rounded-lg p-6 ${getTypeColor(opportunity.type)} hover:shadow-lg transition-shadow`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
              {getTypeLabel(opportunity.type)}
            </span>
            <span className={`text-lg font-bold ${getScoreColor(opportunity.opportunity_score)}`}>
              {(opportunity.opportunity_score * 100).toFixed(0)}%
            </span>
          </div>
          
          {/* Entity Names */}
          <div className="space-y-1">
            {opportunity.theory && (
              <div className="text-lg font-semibold text-gray-900">
                {opportunity.theory}
              </div>
            )}
            {opportunity.phenomenon && (
              <div className="text-base text-gray-700">
                {opportunity.phenomenon}
              </div>
            )}
            {opportunity.method && (
              <div className="text-base text-gray-700">
                Method: {opportunity.method}
              </div>
            )}
            {opportunity.construct_name && (
              <div className="text-sm text-gray-600 italic">
                Type: {opportunity.construct_name}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Evidence Summary */}
      {opportunity.evidence && (
        <div className="mb-4 text-sm text-gray-600">
          {opportunity.evidence.paper_count !== undefined && (
            <div className="mb-1">
              <span className="font-semibold">Papers:</span> {opportunity.evidence.paper_count}
            </div>
          )}
          {opportunity.evidence.connection_strength !== null && opportunity.evidence.connection_strength !== undefined && (
            <div className="mb-1">
              <span className="font-semibold">Connection Strength:</span> {(opportunity.evidence.connection_strength * 100).toFixed(0)}%
            </div>
          )}
          {opportunity.evidence.research_density && (
            <div>
              <span className="font-semibold">Research Density:</span> {opportunity.evidence.research_density}
            </div>
          )}
        </div>
      )}

      {/* Contribution Statement */}
      <div className="mb-4">
        <div className="text-sm font-semibold text-gray-700 mb-2">Contribution Statement</div>
        <div className="text-sm text-gray-700 leading-relaxed">
          {opportunity.contribution_statement}
        </div>
      </div>

      {/* Research Questions */}
      {opportunity.research_questions && opportunity.research_questions.length > 0 && (
        <div className="mb-4">
          <div className="text-sm font-semibold text-gray-700 mb-2">Research Questions</div>
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
            {opportunity.research_questions.map((q, idx) => (
              <li key={idx} className="leading-relaxed">
                {q.replace(/\*\*/g, '')}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Rationale */}
      {opportunity.rationale && (
        <div className="pt-3 border-t border-gray-200">
          <div className="text-xs text-gray-600 italic">
            {opportunity.rationale}
          </div>
        </div>
      )}
    </div>
  );
};

export default OpportunityCard;

