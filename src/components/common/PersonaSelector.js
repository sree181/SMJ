import React from 'react';

/**
 * PersonaSelector Component
 * Allows users to select a reasoning persona for LLM queries
 */
const PersonaSelector = ({ selectedPersona, onPersonaChange, className = '' }) => {
  const personas = [
    {
      id: null,
      name: 'Default',
      description: 'Standard research assistant',
      icon: '📚'
    },
    {
      id: 'historian',
      name: 'Historian',
      description: 'Traces theoretical genealogy and historical debates',
      icon: '📜'
    },
    {
      id: 'reviewer2',
      name: 'Reviewer #2',
      description: 'Critical, gap-finding, and skeptical',
      icon: '🔍'
    },
    {
      id: 'advisor',
      name: 'Advisor',
      description: 'Constructive suggestions and next steps',
      icon: '💡'
    },
    {
      id: 'strategist',
      name: 'Industry Strategist',
      description: 'Translates research to practice',
      icon: '🎯'
    }
  ];

  return (
    <div className={`${className}`}>
      <label className="block text-sm font-semibold text-gray-700 mb-2">
        Reasoning Persona
      </label>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {personas.map((persona) => (
          <button
            key={persona.id || 'default'}
            onClick={() => onPersonaChange(persona.id)}
            className={`
              p-4 rounded-lg border-2 transition-all duration-200 text-left
              ${
                selectedPersona === persona.id
                  ? 'border-blue-500 bg-blue-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
              }
            `}
          >
            <div className="flex items-start space-x-3">
              <span className="text-2xl">{persona.icon}</span>
              <div className="flex-1 min-w-0">
                <div className={`font-semibold text-sm ${
                  selectedPersona === persona.id ? 'text-blue-700' : 'text-gray-900'
                }`}>
                  {persona.name}
                </div>
                <div className="text-xs text-gray-600 mt-1 leading-tight">
                  {persona.description}
                </div>
              </div>
              {selectedPersona === persona.id && (
                <span className="text-blue-500 text-lg">✓</span>
              )}
            </div>
          </button>
        ))}
      </div>
      {selectedPersona && (
        <p className="mt-2 text-xs text-gray-500">
          Selected: {personas.find(p => p.id === selectedPersona)?.name || 'Default'}
        </p>
      )}
    </div>
  );
};

export default PersonaSelector;

