import React from 'react';

const StatsCard = ({ label, value, onClick, color = 'blue' }) => {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-emerald-500 to-emerald-600',
    amber: 'from-amber-500 to-amber-600',
    purple: 'from-purple-500 to-purple-600',
  };

  return (
    <div
      onClick={onClick}
      className={`group relative bg-white rounded-2xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden ${
        onClick ? 'cursor-pointer transform hover:-translate-y-1' : ''
      }`}
    >
      {/* Gradient accent bar */}
      <div className={`h-2 bg-gradient-to-r ${colorClasses[color]}`}></div>
      
      <div className="p-8">
        <div className="text-5xl font-bold text-gray-900 mb-3 tracking-tight">
          {value.toLocaleString()}
        </div>
        <div className="text-base font-semibold text-gray-700 uppercase tracking-wide">
          {label}
        </div>
      </div>
    </div>
  );
};

export default StatsCard;
