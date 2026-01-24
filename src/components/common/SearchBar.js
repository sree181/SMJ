import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const SearchBar = ({ onSearch, placeholder = "Search papers, theories, methods, or ask a question...", className = "" }) => {
  const [query, setQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      // Always use search - it will handle both regular search and questions
      onSearch(query.trim());
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className={`w-full max-w-4xl mx-auto ${className}`}>
      <div 
        className={`relative flex items-center bg-white rounded-2xl shadow-lg border-2 transition-all duration-300 ${
          isFocused 
            ? 'border-blue-500 shadow-xl shadow-blue-100' 
            : 'border-gray-200 hover:border-gray-300'
        } overflow-hidden`}
      >
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          className="flex-1 px-6 py-5 text-lg outline-none text-gray-900 placeholder-gray-400 bg-transparent"
        />
        <button
          type="submit"
          className="mx-2 px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 font-semibold shadow-md hover:shadow-lg transform hover:scale-105 active:scale-100"
        >
          Search
        </button>
      </div>
      
      {/* Help text */}
      <div className="mt-3 text-center">
        <p className="text-sm text-gray-500">
          Search for papers, theories, methods, or ask questions like "What papers use Resource-Based View?"
        </p>
      </div>
    </form>
  );
};

export default SearchBar;
