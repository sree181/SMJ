import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './components/screens/Dashboard';
import SearchResults from './components/screens/SearchResults';
import PaperDetail from './components/screens/PaperDetail';
import QueryResults from './components/screens/QueryResults';
import MetricsDashboard from './components/screens/MetricsDashboard';
import TheoryComparison from './components/screens/TheoryComparison';
import TheoryDetail from './components/screens/TheoryDetail';
import ContributionExplorer from './components/screens/ContributionExplorer';
import TrendsDashboard from './components/screens/TrendsDashboard';
import AdvancedAnalyticsDashboard from './components/screens/AdvancedAnalyticsDashboard';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/search" element={<SearchResults />} />
          <Route path="/paper/:id" element={<PaperDetail />} />
          {/* Placeholder routes for future features */}
          <Route path="/temporal" element={
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-50 to-white">
              <div className="text-center bg-white rounded-2xl shadow-lg p-12 max-w-2xl">
                <h1 className="text-4xl font-bold text-gray-900 mb-4">Temporal Evolution</h1>
                <p className="text-gray-600 text-lg">Coming soon...</p>
              </div>
            </div>
          } />
          <Route path="/graph" element={
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-50 to-white">
              <div className="text-center bg-white rounded-2xl shadow-lg p-12 max-w-2xl">
                <h1 className="text-4xl font-bold text-gray-900 mb-4">Graph Explorer</h1>
                <p className="text-gray-600 text-lg">Coming soon...</p>
              </div>
            </div>
          } />
          <Route path="/analytics" element={<AdvancedAnalyticsDashboard />} />
          <Route path="/analytics-test" element={<div className="min-h-screen flex items-center justify-center"><h1 className="text-4xl">Analytics Test Route Works!</h1></div>} />
          <Route path="/query" element={<QueryResults />} />
          <Route path="/theories/compare" element={<TheoryComparison />} />
          <Route path="/theories/:theoryName" element={<TheoryDetail />} />
          <Route path="/contributions/opportunities" element={<ContributionExplorer />} />
          <Route path="/trends/:entityType/:entityName" element={<TrendsDashboard />} />
          <Route path="/metrics/:entityType" element={<MetricsDashboard />} />
          <Route path="/metrics/:entityType/:entityName" element={<MetricsDashboard />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
