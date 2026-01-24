import React from 'react';
import { useNavigate } from 'react-router-dom';

const PaperCard = ({ paper }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/paper/${paper.paper_id || paper.id}`);
  };

  const authors = paper.authors || [];
  const displayAuthors = authors.slice(0, 3).map(a => 
    typeof a === 'string' ? a : a.full_name || a.name
  );

  const theories = paper.theories || [];
  const methods = paper.methods || [];

  return (
    <article
      className="group bg-white rounded-xl shadow-md hover:shadow-2xl transition-all duration-300 overflow-hidden border border-gray-100 cursor-pointer transform hover:-translate-y-1"
      onClick={handleClick}
    >
      {/* Top accent */}
      <div className="h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>
      
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-4 gap-4">
          <h3 className="text-xl font-bold text-gray-900 leading-tight group-hover:text-blue-600 transition-colors flex-1">
            {paper.title || 'Untitled Paper'}
          </h3>
          {paper.publication_year && (
            <span className="flex-shrink-0 px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-semibold">
              {paper.publication_year}
            </span>
          )}
        </div>

        {/* Authors */}
        {displayAuthors.length > 0 && (
          <div className="mb-4">
            <p className="text-sm text-gray-600 font-medium">
              {displayAuthors.join(', ')}
              {authors.length > 3 && (
                <span className="text-gray-400 ml-1">+{authors.length - 3} more</span>
              )}
            </p>
          </div>
        )}

        {/* Abstract */}
        {paper.abstract && (
          <p className="text-gray-700 text-sm leading-relaxed mb-4 line-clamp-3">
            {paper.abstract.substring(0, 200)}
            {paper.abstract.length > 200 && '...'}
          </p>
        )}

        {/* Tags */}
        <div className="flex flex-wrap gap-2 mb-4">
          {theories.slice(0, 2).map((theory, i) => {
            const theoryName = typeof theory === 'string' 
              ? theory 
              : (theory?.name || theory?.theory_name || '');
            return theoryName ? (
              <span
                key={i}
                className="inline-flex items-center px-3 py-1 bg-blue-50 text-blue-700 rounded-lg text-xs font-medium border border-blue-100"
              >
                {theoryName}
              </span>
            ) : null;
          })}
          {methods.slice(0, 2).map((method, i) => {
            const methodName = typeof method === 'string' 
              ? method 
              : (method?.name || method?.method_name || '');
            return methodName ? (
              <span
                key={i}
                className="inline-flex items-center px-3 py-1 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-medium border border-emerald-100"
              >
                {methodName}
              </span>
            ) : null;
          })}
        </div>

        {/* Action button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            handleClick();
          }}
          className="w-full px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 font-medium text-sm shadow-md hover:shadow-lg transform hover:scale-[1.02] active:scale-100"
        >
          View Details
        </button>
      </div>
    </article>
  );
};

export default PaperCard;
