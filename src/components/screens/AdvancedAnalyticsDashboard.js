import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area, PieChart, Pie, Cell, ComposedChart } from 'recharts';
import { MessageCircle, X, TrendingUp, BookOpen, Lightbulb, BarChart3, Sparkles, ArrowRight, Calendar, Target } from 'lucide-react';
import Loading from '../common/Loading';
import ChatInterface from '../ChatInterface';
import api from '../../services/api';
import '../ChatInterface.css';

const AdvancedAnalyticsDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [paperCounts, setPaperCounts] = useState([]);
  const [authorCounts, setAuthorCounts] = useState([]);
  const [phenomenonCounts, setPhenomenonCounts] = useState([]);
  const [topicEvolution, setTopicEvolution] = useState(null);
  const [theoryEvolution, setTheoryEvolution] = useState(null);
  const [theoryBetweenness, setTheoryBetweenness] = useState(null);
  const [opportunityGaps, setOpportunityGaps] = useState(null);
  const [integrationMechanism, setIntegrationMechanism] = useState(null);
  const [cumulativeTheory, setCumulativeTheory] = useState(null);
  const [canonicalCoverage, setCanonicalCoverage] = useState(null);
  const [canonicalCentrality, setCanonicalCentrality] = useState(null);
  const [theoreticalConcentration, setTheoreticalConcentration] = useState(null);
  const [theoryProblemAlignment, setTheoryProblemAlignment] = useState(null);
  const [integrativeCentrality, setIntegrativeCentrality] = useState(null);
  const [error, setError] = useState(null);
  
  // Chat state
  const [chatOpen, setChatOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  
  // Tab state for dashboard views
  const [activeTab, setActiveTab] = useState('charts'); // 'charts', 'theory-proportions', 'topics-proportions', 'betweenness', 'opportunities', 'integration', 'cumulative', 'canonical', 'hhi', 'alignment', 'integrative', 'authors', 'phenomena'

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('Loading analytics data...');
      
      // Helper function to add timeout to API calls
      const withTimeout = (promise, timeoutMs = 10000) => {
        return Promise.race([
          promise,
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error(`Request timeout after ${timeoutMs}ms`)), timeoutMs)
          )
        ]).catch(err => {
          console.error('API call timeout/failed:', err);
          throw err;
        });
      };
      
      // Load all metrics in parallel with timeout and error handling
      // Note: Complex calculations (topic evolution, theory evolution, etc.) can take 30-60 seconds
      const results = await Promise.allSettled([
        withTimeout(api.getPaperCountsByInterval(), 30000).catch(err => {
          console.error('Error loading paper counts:', err);
          return { intervals: [] };
        }),
        withTimeout(api.getAuthorCountsByInterval(), 30000).catch(err => {
          console.error('Error loading author counts:', err);
          return { intervals: [] };
        }),
        withTimeout(api.getPhenomenonCountsByInterval(), 30000).catch(err => {
          console.error('Error loading phenomenon counts:', err);
          return { intervals: [] };
        }),
        withTimeout(api.getTopicEvolution(), 60000).catch(err => {
          console.error('Error loading topic evolution:', err);
          return null;
        }),
        withTimeout(api.getTheoryEvolutionDivergence(), 60000).catch(err => {
          console.error('Error loading theory evolution:', err);
          return null;
        }),
        withTimeout(api.getTheoryBetweenness(), 30000).catch(err => {
          console.error('Error loading theory betweenness:', err);
          return null;
        }),
        withTimeout(api.getOpportunityGaps(), 30000).catch(err => {
          console.error('Error loading opportunity gaps:', err);
          return null;
        }),
        withTimeout(api.getIntegrationMechanism(), 60000).catch(err => {
          console.error('Error loading integration mechanism:', err);
          return null;
        }),
        withTimeout(api.getCumulativeTheory(), 60000).catch(err => {
          console.error('Error loading cumulative theory:', err);
          return null;
        }),
        withTimeout(api.getCanonicalCoverage(), 30000).catch(err => {
          console.error('Error loading canonical coverage:', err);
          return null;
        }),
        withTimeout(api.getCanonicalCentrality(), 90000).catch(err => {
          console.error('Error loading canonical centrality:', err);
          return { error: err.message || 'NetworkX not available or timeout' };
        }),
        Promise.resolve(null), // getTheoreticalConcentration - commented out in backend
        Promise.resolve(null), // getTheoryProblemAlignment - commented out due to syntax errors
        Promise.resolve(null) // getIntegrativeTheoryCentrality - commented out due to UI errors
      ]);
      
      // Extract values from Promise.allSettled results
      const [
        countsData, authorCountsData, phenomenonCountsData, topicsData, theoriesData, betweennessData, gapsData, 
        integrationData, cumulativeData, coverageData, centralityData, 
        hhiData, alignmentData, integrativeData
      ] = results.map(result => {
        if (result.status === 'fulfilled') {
          return result.value;
        } else {
          console.error('Promise rejected:', result.reason);
          return null;
        }
      });

      console.log('Data loaded:', { 
        counts: countsData?.intervals?.length || 0,
        topics: topicsData ? 'loaded' : 'failed',
        theories: theoriesData ? 'loaded' : 'failed',
        betweenness: betweennessData ? 'loaded' : 'failed',
        gaps: gapsData ? 'loaded' : 'failed',
        integration: integrationData ? 'loaded' : 'failed',
        cumulative: cumulativeData ? 'loaded' : 'failed',
        coverage: coverageData ? 'loaded' : 'failed',
        centrality: centralityData ? 'loaded' : 'failed',
        hhi: hhiData ? 'loaded' : 'failed',
        alignment: alignmentData ? 'loaded' : 'failed',
        integrative: integrativeData ? 'loaded' : 'failed'
      });

      setPaperCounts(countsData?.intervals || []);
      setAuthorCounts(authorCountsData?.intervals || []);
      const phenomenonIntervals = phenomenonCountsData?.intervals || [];
      console.log('Phenomenon counts loaded:', phenomenonIntervals.length, 'intervals');
      if (phenomenonIntervals.length > 0) {
        console.log('First interval sample:', phenomenonIntervals[0]);
      } else {
        console.warn('No phenomenon intervals returned from API. Full response:', phenomenonCountsData);
      }
      setPhenomenonCounts(phenomenonIntervals);
      setTopicEvolution(topicsData);
      setTheoryEvolution(theoriesData);
      setTheoryBetweenness(betweennessData);
      setOpportunityGaps(gapsData);
      setIntegrationMechanism(integrationData);
      setCumulativeTheory(cumulativeData);
      setCanonicalCoverage(coverageData);
      setCanonicalCentrality(centralityData);
      setTheoreticalConcentration(null);
      setTheoryProblemAlignment(alignmentData);
      setIntegrativeCentrality(null); // Commented out due to UI errors
    } catch (err) {
      console.error('Error loading analytics:', err);
      setError(err.message || 'Failed to load analytics data. Please check if the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  // Chat handlers
  const handleSendMessage = async (messageText) => {
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: messageText,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setChatLoading(true);

    try {
      const response = await api.queryGraphRAG(messageText, null);
      
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.answer || 'I apologize, but I could not generate a response.',
        timestamp: new Date().toISOString(),
        sources: response.sources || []
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: `Error: ${err.message || 'Failed to process your question. Please try again.'}`,
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
  };

  if (loading) {
    return <Loading message="Loading advanced analytics..." />;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-6 shadow-lg">
            <p className="text-red-800 font-semibold mb-2">Error Loading Dashboard</p>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={loadAllData}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-semibold"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Calculate summary statistics
  const totalPapers = paperCounts.reduce((sum, i) => sum + i.count, 0);
  const avgPerInterval = paperCounts.length > 0 ? Math.round(totalPapers / paperCounts.length) : 0;
  const peakInterval = paperCounts.length > 0 
    ? paperCounts.reduce((max, i) => i.count > max.count ? i : max, paperCounts[0])
    : null;

  // Prepare chart data
  const paperCountsChartData = paperCounts.map(interval => ({
    interval: interval.interval,
    count: interval.count
  }));

  const topicEvolutionChartData = topicEvolution?.intervals?.map(interval => ({
    interval: interval.interval,
    topicCount: interval.topic_count,
    coherence: (interval.coherence * 100).toFixed(1),
    diversity: (interval.diversity * 100).toFixed(1),
    stability: interval.stability ? (interval.stability * 100).toFixed(1) : 0
  })) || [];

  // Prepare topics per period data for visualization
  const topicsPerPeriodData = topicEvolution?.intervals?.map(interval => {
    const data = {
      interval: interval.interval,
      totalPapers: interval.total_papers || 0
    };
    
    // Add each topic as a separate data point with its paper count
    if (interval.topics && Array.isArray(interval.topics)) {
      interval.topics.forEach((topic, index) => {
        data[`Topic ${index + 1}`] = topic.paper_count || 0;
      });
    }
    
    return data;
  }) || [];

  // Get all unique topic keys for stacked bar chart
  const topicKeys = topicEvolution?.intervals?.reduce((keys, interval) => {
    if (interval.topics && Array.isArray(interval.topics)) {
      interval.topics.forEach((_, index) => {
        const key = `Topic ${index + 1}`;
        if (!keys.includes(key)) {
          keys.push(key);
        }
      });
    }
    return keys;
  }, []) || [];

  // Generate colors for topics
  const topicColors = [
    '#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', '#EF4444',
    '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1',
    '#A855F7', '#14B8A6', '#F43F5E', '#8B5CF6', '#6366F1'
  ];

  const theoryEvolutionChartData = theoryEvolution?.intervals?.map(interval => {
    // Ensure we're using the correct field name (fragmentation_index from backend)
    const fragValue = interval.fragmentation_index !== undefined 
      ? interval.fragmentation_index 
      : (interval.fragmentation !== undefined ? interval.fragmentation : 0);
    
    return {
      interval: interval.interval,
      theoryCount: interval.theory_count,
      diversity: parseFloat((interval.diversity * 100).toFixed(1)),
      concentration: parseFloat((interval.concentration * 100).toFixed(1)),
      fragmentation: parseFloat((fragValue * 100).toFixed(1)),
      divergence: interval.divergence ? parseFloat((interval.divergence * 100).toFixed(2)) : 0,
      emergenceRate: interval.emergence_rate ? parseFloat((interval.emergence_rate * 100).toFixed(2)) : 0
    };
  }) || [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-gray-50 relative">
      {/* Header Bar */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-30">
        <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <BarChart3 size={24} className="text-blue-600" />
              </div>
              <div>
                <h1 className="text-xl md:text-2xl font-bold text-gray-900">
                  Strategic Management Research Analytics
                </h1>
                <p className="text-sm text-gray-600 hidden md:block">
                  Graph RAG-powered insights • 1985-2025
                </p>
              </div>
            </div>
            <button
              onClick={() => setChatOpen(!chatOpen)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition-all shadow-sm ${
                chatOpen 
                  ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-md' 
                  : 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white hover:from-blue-600 hover:to-indigo-700 shadow-md hover:shadow-lg'
              }`}
            >
              {chatOpen ? (
                <>
                  <X size={18} />
                  <span className="hidden sm:inline">Close Assistant</span>
                </>
              ) : (
                <>
                  <MessageCircle size={18} />
                  <span className="hidden sm:inline">Research Assistant</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-2 mb-6 inline-flex overflow-x-auto max-w-full">
          <button
            onClick={() => setActiveTab('charts')}
            className={`px-6 py-2 rounded-lg font-semibold transition-all ${
              activeTab === 'charts'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <BarChart3 size={18} className="inline mr-2" />
            Analytics Charts
          </button>
          <button
            onClick={() => setActiveTab('theory-proportions')}
            className={`px-6 py-2 rounded-lg font-semibold transition-all ${
              activeTab === 'theory-proportions'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <BookOpen size={18} className="inline mr-2" />
            Theory Proportions
          </button>
          <button
            onClick={() => setActiveTab('topics-proportions')}
            className={`px-6 py-2 rounded-lg font-semibold transition-all ${
              activeTab === 'topics-proportions'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Sparkles size={18} className="inline mr-2" />
            Topics Proportions
          </button>
          <button
            onClick={() => setActiveTab('betweenness')}
            className={`px-6 py-2 rounded-lg font-semibold transition-all ${
              activeTab === 'betweenness'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Target size={18} className="inline mr-2" />
            Theory Betweenness
          </button>
          <button
            onClick={() => setActiveTab('opportunities')}
            className={`px-6 py-2 rounded-lg font-semibold transition-all ${
              activeTab === 'opportunities'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Lightbulb size={18} className="inline mr-2" />
            Opportunity Gaps
          </button>
          <button
            onClick={() => setActiveTab('integration')}
            className={`px-6 py-2 rounded-lg font-semibold transition-all ${
              activeTab === 'integration'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Sparkles size={18} className="inline mr-2" />
            Integration
          </button>
          <button
            onClick={() => setActiveTab('cumulative')}
            className={`px-6 py-2 rounded-lg font-semibold transition-all ${
              activeTab === 'cumulative'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <TrendingUp size={18} className="inline mr-2" />
            Cumulative Theory
          </button>
          <button
            onClick={() => setActiveTab('canonical')}
            className={`px-6 py-2 rounded-lg font-semibold transition-all ${
              activeTab === 'canonical'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Calendar size={18} className="inline mr-2" />
            Canonical
          </button>
          <button
            onClick={() => setActiveTab('hhi')}
            className={`px-6 py-2 rounded-lg font-semibold transition-all ${
              activeTab === 'hhi'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <BarChart3 size={18} className="inline mr-2" />
            HHI Concentration
          </button>
          <button
            onClick={() => setActiveTab('alignment')}
            className={`px-6 py-2 rounded-lg font-semibold transition-all ${
              activeTab === 'alignment'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Target size={18} className="inline mr-2" />
            Alignment
          </button>
          <button
            onClick={() => setActiveTab('integrative')}
            className={`px-6 py-2 rounded-lg font-semibold transition-all ${
              activeTab === 'integrative'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Sparkles size={18} className="inline mr-2" />
            Integrative
          </button>
          <button
            onClick={() => setActiveTab('authors')}
            className={`px-6 py-2 rounded-lg font-semibold transition-all ${
              activeTab === 'authors'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <BookOpen size={18} className="inline mr-2" />
            Authors
          </button>
          <button
            onClick={() => setActiveTab('phenomena')}
            className={`px-6 py-2 rounded-lg font-semibold transition-all ${
              activeTab === 'phenomena'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Sparkles size={18} className="inline mr-2" />
            Phenomena
          </button>
        </div>
      </div>

      {/* Main Dashboard Grid */}
      <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 pb-6">
        {activeTab === 'charts' ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left Column - Main Charts (8 columns on large screens) */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* Top Row: Key Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg">
                <div className="flex items-center gap-2 mb-2">
                  <BookOpen size={20} />
                  <span className="text-blue-100 text-sm font-medium">Total Papers</span>
                </div>
                <p className="text-3xl font-bold">{totalPapers.toLocaleString()}</p>
                <p className="text-blue-100 text-xs mt-1">Across all intervals</p>
              </div>
              
              <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white shadow-lg">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp size={20} />
                  <span className="text-purple-100 text-sm font-medium">Avg per Interval</span>
                </div>
                <p className="text-3xl font-bold">{avgPerInterval}</p>
                <p className="text-purple-100 text-xs mt-1">5-year periods</p>
              </div>
              
              <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl p-6 text-white shadow-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Target size={20} />
                  <span className="text-indigo-100 text-sm font-medium">Peak Period</span>
                </div>
                <p className="text-3xl font-bold">{peakInterval?.interval || 'N/A'}</p>
                <p className="text-indigo-100 text-xs mt-1">{peakInterval ? `${peakInterval.count} papers` : ''}</p>
              </div>
            </div>

            {/* Paper Counts Chart */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Calendar size={20} className="text-blue-600" />
                <h2 className="text-lg font-bold text-gray-900">Research Volume Evolution</h2>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={paperCountsChartData} margin={{ top: 10, right: 10, left: 0, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    dataKey="interval" 
                    angle={-45} 
                    textAnchor="end" 
                    height={80}
                    tick={{ fill: '#6b7280', fontSize: 11 }}
                  />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#fff', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                    }}
                  />
                  <Bar 
                    dataKey="count" 
                    fill="#3B82F6" 
                    name="Papers"
                    radius={[6, 6, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Topic Evolution Chart */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles size={20} className="text-purple-600" />
                <h2 className="text-lg font-bold text-gray-900">Topic Landscape Evolution</h2>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={topicEvolutionChartData} margin={{ top: 10, right: 10, left: 0, bottom: 60 }}>
                  <defs>
                    <linearGradient id="colorTopicCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.1}/>
                    </linearGradient>
                    <linearGradient id="colorCoherence" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0.1}/>
                    </linearGradient>
                    <linearGradient id="colorDiversity" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    dataKey="interval" 
                    angle={-45} 
                    textAnchor="end" 
                    height={80}
                    tick={{ fill: '#6b7280', fontSize: 11 }}
                  />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#fff', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                    }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />
                  <Area 
                    type="monotone" 
                    dataKey="topicCount" 
                    stroke="#8B5CF6" 
                    fillOpacity={1} 
                    fill="url(#colorTopicCount)" 
                    name="Topics"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="coherence" 
                    stroke="#10B981" 
                    fillOpacity={1} 
                    fill="url(#colorCoherence)" 
                    name="Coherence %"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="diversity" 
                    stroke="#F59E0B" 
                    fillOpacity={1} 
                    fill="url(#colorDiversity)" 
                    name="Diversity %"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Topics Per Period Chart */}
            {topicEvolution?.intervals && topicEvolution.intervals.length > 0 && (
              <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Sparkles size={20} className="text-purple-600" />
                  <h2 className="text-lg font-bold text-gray-900">Topics by Period</h2>
                </div>
                <p className="text-sm text-gray-600 mb-4">
                  Shows the distribution of papers across topics for each 5-year period. Each segment represents a topic cluster.
                </p>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart 
                    data={topicsPerPeriodData} 
                    margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      dataKey="interval" 
                      angle={-45} 
                      textAnchor="end" 
                      height={100}
                      tick={{ fill: '#6b7280', fontSize: 11 }}
                    />
                    <YAxis 
                      label={{ value: 'Number of Papers', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#6b7280', fontSize: 11 } }}
                      tick={{ fill: '#6b7280', fontSize: 11 }}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#fff', 
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                      }}
                      formatter={(value, name) => {
                        if (name === 'totalPapers') return [value, 'Total Papers'];
                        return [value, name];
                      }}
                    />
                    <Legend 
                      wrapperStyle={{ paddingTop: '20px', fontSize: '11px' }}
                      iconType="square"
                    />
                    {topicKeys.slice(0, 10).map((key, index) => (
                      <Bar 
                        key={key}
                        dataKey={key}
                        stackId="topics"
                        fill={topicColors[index % topicColors.length]}
                        name={key}
                      />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
                {topicKeys.length > 10 && (
                  <p className="text-xs text-gray-500 mt-2 text-center">
                    Showing top 10 topics. Total topics vary by period.
                  </p>
                )}
                
                {/* Detailed Topics Table */}
                <div className="mt-6 border-t border-gray-200 pt-6">
                  <h3 className="text-md font-semibold text-gray-900 mb-4">Topic Details by Period</h3>
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {topicEvolution.intervals.map((interval) => (
                      <div key={interval.interval} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-semibold text-gray-900">{interval.interval}</h4>
                          <span className="text-sm text-gray-600">
                            {interval.topic_count} topics • {interval.total_papers || 0} papers
                          </span>
                        </div>
                        {interval.topics && interval.topics.length > 0 ? (
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                            {interval.topics.map((topic, idx) => (
                              <div 
                                key={idx} 
                                className="bg-white rounded-lg p-3 border border-gray-200 shadow-sm"
                                style={{ borderLeft: `4px solid ${topicColors[idx % topicColors.length]}` }}
                              >
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-sm font-semibold text-gray-900">
                                    Topic {idx + 1}
                                  </span>
                                  <span className="text-xs text-gray-600">
                                    {topic.paper_count} papers
                                  </span>
                                </div>
                                <div className="text-xs text-gray-600 mb-2">
                                  Coherence: {(topic.coherence * 100).toFixed(1)}%
                                </div>
                                {topic.representative_paper && (
                                  <div className="text-xs text-gray-500 italic truncate" title={topic.representative_paper.title}>
                                    📄 {topic.representative_paper.title || topic.representative_paper.paper_id}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500">No topics identified for this period</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Theory Evolution Chart */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Lightbulb size={20} className="text-indigo-600" />
                <h2 className="text-lg font-bold text-gray-900">Theoretical Evolution & Divergence</h2>
              </div>
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={theoryEvolutionChartData} margin={{ top: 10, right: 50, left: 0, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    dataKey="interval" 
                    angle={-45} 
                    textAnchor="end" 
                    height={80}
                    tick={{ fill: '#6b7280', fontSize: 11 }}
                  />
                  {/* Left Y-Axis: For Diversity, Concentration, Fragmentation, Divergence (0-100%) */}
                  <YAxis 
                    yAxisId="left"
                    label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#6b7280', fontSize: 11 } }}
                    tick={{ fill: '#6b7280', fontSize: 11 }}
                    domain={[0, 100]}
                  />
                  {/* Right Y-Axis: For Emergence Rate (can have different scale) */}
                  <YAxis 
                    yAxisId="right"
                    orientation="right"
                    label={{ value: 'Emergence Rate', angle: 90, position: 'insideRight', style: { textAnchor: 'middle', fill: '#8B5CF6', fontSize: 11 } }}
                    tick={{ fill: '#8B5CF6', fontSize: 11 }}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#fff', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                    }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />
                  <Line 
                    yAxisId="left"
                    type="monotone" 
                    dataKey="diversity" 
                    stroke="#3B82F6" 
                    strokeWidth={2} 
                    dot={{ fill: '#3B82F6', r: 3 }}
                    name="Diversity %"
                  />
                  <Line 
                    yAxisId="left"
                    type="monotone" 
                    dataKey="concentration" 
                    stroke="#EF4444" 
                    strokeWidth={2} 
                    dot={{ fill: '#EF4444', r: 3 }}
                    name="Concentration %"
                  />
                  <Line 
                    yAxisId="left"
                    type="monotone" 
                    dataKey="fragmentation" 
                    stroke="#10B981" 
                    strokeWidth={2} 
                    dot={{ fill: '#10B981', r: 3 }}
                    name="Fragmentation %"
                  />
                  <Line 
                    yAxisId="left"
                    type="monotone" 
                    dataKey="divergence" 
                    stroke="#F59E0B" 
                    strokeWidth={2} 
                    dot={{ fill: '#F59E0B', r: 3 }}
                    name="Divergence %"
                  />
                  <Line 
                    yAxisId="right"
                    type="monotone" 
                    dataKey="emergenceRate" 
                    stroke="#8B5CF6" 
                    strokeWidth={2} 
                    dot={{ fill: '#8B5CF6', r: 4 }}
                    name="Emergence Rate %"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Right Column - Insights & Metrics (4 columns on large screens) */}
          <div className="lg:col-span-4 space-y-6">
            
            {/* Topic Metrics Summary */}
            {topicEvolution?.summary && (
              <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Sparkles size={18} className="text-purple-600" />
                  <h3 className="text-lg font-bold text-gray-900">Topic Metrics</h3>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                    <span className="text-sm text-gray-700">Avg Topics/Interval</span>
                    <span className="text-lg font-bold text-purple-900">
                      {topicEvolution.summary.avg_topics_per_interval.toFixed(1)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                    <span className="text-sm text-gray-700">Avg Coherence</span>
                    <span className="text-lg font-bold text-green-900">
                      {(topicEvolution.summary.avg_coherence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-yellow-50 rounded-lg">
                    <span className="text-sm text-gray-700">Avg Diversity</span>
                    <span className="text-lg font-bold text-yellow-900">
                      {(topicEvolution.summary.avg_diversity * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                    <span className="text-sm text-gray-700">Total Intervals</span>
                    <span className="text-lg font-bold text-blue-900">
                      {topicEvolution.summary.total_intervals}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Theory Metrics Summary */}
            {theoryEvolution?.summary && (
              <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Lightbulb size={18} className="text-indigo-600" />
                  <h3 className="text-lg font-bold text-gray-900">Theory Metrics</h3>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                    <span className="text-sm text-gray-700">Avg Diversity</span>
                    <span className="text-lg font-bold text-blue-900">
                      {(theoryEvolution.summary.avg_diversity * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                    <span className="text-sm text-gray-700">Avg Concentration</span>
                    <span className="text-lg font-bold text-red-900">
                      {(theoryEvolution.summary.avg_concentration * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                    <span className="text-sm text-gray-700">Avg Fragmentation</span>
                    <span className="text-lg font-bold text-green-900">
                      {(theoryEvolution.summary.avg_fragmentation * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                    <span className="text-sm text-gray-700">Trend</span>
                    <span className="text-lg font-bold text-purple-900 capitalize">
                      {theoryEvolution.summary.trend || 'stable'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Recent Topic Dynamics */}
            {topicEvolution?.intervals && topicEvolution.intervals.length > 0 && (
              <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp size={18} className="text-yellow-600" />
                  <h3 className="text-lg font-bold text-gray-900">Recent Dynamics</h3>
                </div>
                <div className="space-y-3">
                  {topicEvolution.intervals.slice(-3).map(interval => (
                    <div key={interval.interval} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <h4 className="font-semibold text-gray-900 mb-2 text-sm">{interval.interval}</h4>
                      <div className="space-y-1">
                        {interval.emerging_topics && interval.emerging_topics.length > 0 && (
                          <div className="flex items-center gap-2 text-xs">
                            <span className="text-green-600">🌱</span>
                            <span className="text-gray-700">{interval.emerging_topics.length} emerging</span>
                          </div>
                        )}
                        {interval.declining_topics && interval.declining_topics.length > 0 && (
                          <div className="flex items-center gap-2 text-xs">
                            <span className="text-red-600">📉</span>
                            <span className="text-gray-700">{interval.declining_topics.length} declining</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top Theories Preview */}
            {theoryEvolution?.intervals && (
              <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <BookOpen size={18} className="text-indigo-600" />
                  <h3 className="text-lg font-bold text-gray-900">Top Theories by Period</h3>
                </div>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {theoryEvolution.intervals
                    .filter(interval => interval.theories && Object.keys(interval.theories).length > 0)
                    .map(interval => {
                      const topTheories = Object.entries(interval.theories || {})
                        .sort((a, b) => b[1].usage_count - a[1].usage_count)
                        .slice(0, 3);
                      
                      if (topTheories.length === 0) return null;
                      
                      return (
                        <div key={interval.interval} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                          <h4 className="font-semibold text-gray-900 mb-2 text-sm">{interval.interval}</h4>
                          <ul className="space-y-1">
                            {topTheories.map(([theory, data]) => (
                              <li key={theory} className="flex items-center justify-between text-xs">
                                <span className="font-medium text-gray-900 truncate flex-1">{theory}</span>
                                <span className="text-gray-500 ml-2 flex-shrink-0">({data.usage_count})</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      );
                    })
                    .filter(Boolean)}
                </div>
              </div>
            )}

            {/* Refresh Button */}
            <button
              onClick={loadAllData}
              className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all font-semibold shadow-lg hover:shadow-xl"
            >
              <BarChart3 size={18} className="inline mr-2" />
              Refresh Analytics
            </button>
          </div>
        </div>
        ) : activeTab === 'theory-proportions' ? (
        <div className="space-y-6">
          {/* Theory Proportions Tab */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-6">
              <BookOpen size={24} className="text-indigo-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Theory Proportions by 5-Year Intervals</h2>
                <p className="text-gray-600 mt-1">Distribution of theories across research periods</p>
              </div>
            </div>

            {/* Pie Charts Grid */}
            {theoryEvolution?.intervals && theoryEvolution.intervals.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {theoryEvolution.intervals
                  .filter(interval => interval.theories && Object.keys(interval.theories).length > 0)
                  .map(interval => {
                    const theories = Object.entries(interval.theories || {})
                      .sort((a, b) => b[1].usage_count - a[1].usage_count)
                      .slice(0, 20); // Only top 20 theories
                    
                    const totalUsage = theories.reduce((sum, [, data]) => sum + data.usage_count, 0);
                    
                    const pieData = theories.map(([theory, data]) => ({
                      name: theory,
                      value: data.usage_count,
                      percentage: ((data.usage_count / totalUsage) * 100).toFixed(1)
                    }));

                    // Extended color palette for up to 20 theories
                    const COLORS = [
                      '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
                      '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1',
                      '#14B8A6', '#F43F5E', '#A855F7', '#EAB308', '#22C55E',
                      '#F97316', '#06B6D4', '#8B5CF6', '#EC4899', '#10B981'
                    ];

                    return (
                      <div key={interval.interval} className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                        <h3 className="text-lg font-bold text-gray-900 mb-2 text-center">
                          {interval.interval}
                        </h3>
                        <div className="mb-4">
                          <p className="text-sm text-gray-600 text-center">
                            Top {theories.length} theories • {totalUsage} total uses
                          </p>
                        </div>
                        <ResponsiveContainer width="100%" height={280}>
                          <PieChart>
                            <Pie
                              data={pieData}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={false}
                              outerRadius={100}
                              innerRadius={30}
                              fill="#8884d8"
                              dataKey="value"
                              paddingAngle={2}
                            >
                              {pieData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip 
                              formatter={(value, name, props) => [
                                `${value} uses (${props.payload.percentage}%)`,
                                props.payload.name
                              ]}
                              contentStyle={{
                                backgroundColor: '#fff',
                                border: '1px solid #e5e7eb',
                                borderRadius: '8px',
                                boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                                maxWidth: '300px'
                              }}
                            />
                          </PieChart>
                        </ResponsiveContainer>
                        
                        {/* Top 10 Theories List */}
                        <div className="mt-4 pt-4 border-t border-gray-200">
                          <h4 className="text-sm font-semibold text-gray-700 mb-2">Top 10 Theories:</h4>
                          <ul className="space-y-1 max-h-48 overflow-y-auto">
                            {theories.slice(0, 10).map(([theory, data], idx) => (
                              <li key={theory} className="flex items-center justify-between text-xs py-1">
                                <span className="flex items-center gap-2 flex-1 min-w-0">
                                  <div 
                                    className="w-3 h-3 rounded-full flex-shrink-0" 
                                    style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                                  />
                                  <span className="text-gray-900 truncate">{theory}</span>
                                </span>
                                <span className="text-gray-500 ml-2 flex-shrink-0 text-right">
                                  {data.usage_count} ({(data.usage_count / totalUsage * 100).toFixed(1)}%)
                                </span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </div>
        </div>
        ) : activeTab === 'topics-proportions' ? (
        <div className="space-y-6">
          {/* Topics Proportions Tab */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-6">
              <Sparkles size={24} className="text-purple-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Topics Proportions by 5-Year Intervals</h2>
                <p className="text-gray-600 mt-1">Distribution of top 10 topics across research periods</p>
              </div>
            </div>

            {/* Pie Charts Grid */}
            {topicEvolution?.intervals && topicEvolution.intervals.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {topicEvolution.intervals
                  .filter(interval => interval.topics && interval.topics.length > 0)
                  .map(interval => {
                    // Get top 10 topics sorted by paper_count
                    const topics = (interval.topics || [])
                      .sort((a, b) => (b.paper_count || 0) - (a.paper_count || 0))
                      .slice(0, 10); // Only top 10 topics
                    
                    const totalPapers = topics.reduce((sum, topic) => sum + (topic.paper_count || 0), 0);
                    
                    const pieData = topics.map((topic, idx) => {
                      // Use generated topic name if available, otherwise fallback to representative paper title
                      let topicName = `Topic ${idx + 1}`;
                      if (topic.name && topic.name !== topic.representative_paper?.title) {
                        // Use generated topic name (truncate if too long)
                        topicName = topic.name.length > 40 ? topic.name.substring(0, 40) + '...' : topic.name;
                      } else if (topic.representative_paper && topic.representative_paper.title) {
                        // Fallback to representative paper title
                        const title = topic.representative_paper.title;
                        topicName = title.length > 40 ? title.substring(0, 40) + '...' : title;
                      }
                      
                      return {
                        name: topicName,
                        value: topic.paper_count || 0,
                        percentage: totalPapers > 0 ? (((topic.paper_count || 0) / totalPapers) * 100).toFixed(1) : '0.0',
                        coherence: topic.coherence ? (topic.coherence * 100).toFixed(1) : '0.0',
                        fullTitle: topic.name || topic.representative_paper?.title || `Topic ${idx + 1}`
                      };
                    });

                    // Color palette for topics
                    const TOPIC_COLORS = [
                      '#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', '#EF4444',
                      '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
                    ];

                    return (
                      <div key={interval.interval} className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                        <h3 className="text-lg font-bold text-gray-900 mb-2 text-center">
                          {interval.interval}
                        </h3>
                        <div className="mb-4">
                          <p className="text-sm text-gray-600 text-center">
                            Top {topics.length} topics • {totalPapers} papers • {interval.topic_count || 0} total topics
                          </p>
                        </div>
                        <ResponsiveContainer width="100%" height={280}>
                          <PieChart>
                            <Pie
                              data={pieData}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={false}
                              outerRadius={100}
                              innerRadius={30}
                              fill="#8884d8"
                              dataKey="value"
                              paddingAngle={2}
                            >
                              {pieData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={TOPIC_COLORS[index % TOPIC_COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip 
                              formatter={(value, name, props) => [
                                `${value} papers (${props.payload.percentage}%)`,
                                props.payload.fullTitle || props.payload.name
                              ]}
                              contentStyle={{
                                backgroundColor: '#fff',
                                border: '1px solid #e5e7eb',
                                borderRadius: '8px',
                                boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                                maxWidth: '350px'
                              }}
                            />
                          </PieChart>
                        </ResponsiveContainer>
                        
                        {/* Top 10 Topics List */}
                        <div className="mt-4 pt-4 border-t border-gray-200">
                          <h4 className="text-sm font-semibold text-gray-700 mb-2">Top 10 Topics:</h4>
                          <ul className="space-y-1 max-h-48 overflow-y-auto">
                            {topics.map((topic, idx) => {
                              // Use generated topic name if available, otherwise use representative paper title
                              const topicName = topic.name || topic.representative_paper?.title || `Topic ${idx + 1}`;
                              const displayName = topic.name ? topic.name : (topic.representative_paper?.title || `Topic ${idx + 1}`);
                              
                              return (
                                <li key={idx} className="flex items-start justify-between text-xs py-1">
                                  <span className="flex items-center gap-2 flex-1 min-w-0">
                                    <div 
                                      className="w-3 h-3 rounded-full flex-shrink-0 mt-0.5" 
                                      style={{ backgroundColor: TOPIC_COLORS[idx % TOPIC_COLORS.length] }}
                                    />
                                    <span className="text-gray-900">
                                      {topic.name ? (
                                        <>
                                          <span className="font-medium">{topic.name}</span>
                                          {topic.representative_paper?.title && topic.representative_paper.title !== topic.name && (
                                            <span className="text-gray-500 text-xs ml-1 italic" title={topic.representative_paper.title}>
                                              ({topic.representative_paper.title.length > 30 ? topic.representative_paper.title.substring(0, 30) + '...' : topic.representative_paper.title})
                                            </span>
                                          )}
                                        </>
                                      ) : (
                                        <>
                                          <span className="font-medium">Topic {idx + 1}:</span>
                                          <span className="text-gray-700 ml-1" title={displayName}>
                                            {displayName.length > 50 ? displayName.substring(0, 50) + '...' : displayName}
                                          </span>
                                        </>
                                      )}
                                      <span className="text-gray-500 ml-1">
                                        ({(topic.coherence * 100).toFixed(1)}% coherence)
                                      </span>
                                    </span>
                                  </span>
                                  <span className="text-gray-500 ml-2 flex-shrink-0 text-right">
                                    {topic.paper_count || 0} papers
                                  </span>
                                </li>
                              );
                            })}
                          </ul>
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
            
            {(!topicEvolution?.intervals || topicEvolution.intervals.length === 0) && (
              <div className="text-center py-12">
                <p className="text-gray-600">No topic data available.</p>
                <p className="text-sm text-gray-500 mt-2">Topic data will appear here once available.</p>
              </div>
            )}
          </div>
        </div>
        ) : activeTab === 'betweenness' ? (
        <div className="space-y-6">
          {/* Theory Betweenness Tab */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-6">
              <Target size={24} className="text-indigo-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Theory Betweenness & Cross-Topic Reach</h2>
                <p className="text-gray-600 mt-1">Theories that connect multiple phenomena and research domains</p>
              </div>
            </div>

            {theoryBetweenness && (
              <>
                {/* Summary Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <p className="text-sm text-blue-600 font-medium mb-1">Bridge Theories</p>
                    <p className="text-2xl font-bold text-blue-900">{theoryBetweenness.summary?.total_bridge_theories || 0}</p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                    <p className="text-sm text-purple-600 font-medium mb-1">Avg Cross-Topic Reach</p>
                    <p className="text-2xl font-bold text-purple-900">
                      {theoryBetweenness.summary?.avg_cross_topic_reach?.toFixed(1) || '0.0'}
                    </p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                    <p className="text-sm text-green-600 font-medium mb-1">Max Reach</p>
                    <p className="text-2xl font-bold text-green-900">
                      {theoryBetweenness.summary?.max_cross_topic_reach || 0} phenomena
                    </p>
                  </div>
                </div>

                {/* Bar Chart */}
                {theoryBetweenness.theories && theoryBetweenness.theories.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Top 20 Bridge Theories</h3>
                    <ResponsiveContainer width="100%" height={500}>
                      <BarChart data={theoryBetweenness.theories.slice(0, 20)}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis 
                          dataKey="theory_name" 
                          angle={-45} 
                          textAnchor="end" 
                          height={120}
                          tick={{ fill: '#6b7280', fontSize: 11 }}
                        />
                        <YAxis 
                          label={{ value: 'Phenomena Count', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#6b7280', fontSize: 11 } }}
                          tick={{ fill: '#6b7280', fontSize: 11 }}
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#fff', 
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                            boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                          }}
                          formatter={(value, name) => [
                            `${value} phenomena`,
                            'Cross-Topic Reach'
                          ]}
                        />
                        <Bar dataKey="cross_topic_reach" fill="#3B82F6" radius={[8, 8, 0, 0]}>
                          {theoryBetweenness.theories.slice(0, 20).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={index < 5 ? '#3B82F6' : '#60A5FA'} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Theory Details Table */}
                {theoryBetweenness.theories && theoryBetweenness.theories.length > 0 && (
                  <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">All Bridge Theories</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-gray-300">
                            <th className="text-left py-3 px-4 font-semibold text-gray-700">Theory</th>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">Cross-Topic Reach</th>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">Papers</th>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">Betweenness Score</th>
                          </tr>
                        </thead>
                        <tbody>
                          {theoryBetweenness.theories.map((theory, idx) => (
                            <tr key={theory.theory_name} className="border-b border-gray-200 hover:bg-gray-100">
                              <td className="py-3 px-4 font-medium text-gray-900">{theory.theory_name}</td>
                              <td className="text-center py-3 px-4 text-gray-700">{theory.cross_topic_reach}</td>
                              <td className="text-center py-3 px-4 text-gray-700">{theory.paper_count}</td>
                              <td className="text-center py-3 px-4">
                                <span className="inline-block px-2 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                                  {(theory.betweenness_score * 100).toFixed(1)}%
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
        ) : activeTab === 'opportunities' ? (
        <div className="space-y-6">
          {/* Opportunity Gaps Tab */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-6">
              <Lightbulb size={24} className="text-yellow-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Research Opportunity Gaps</h2>
                <p className="text-gray-600 mt-1">Under-theorized phenomena that represent research opportunities</p>
              </div>
            </div>

            {opportunityGaps && (
              <>
                {/* Summary Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                    <p className="text-sm text-yellow-600 font-medium mb-1">Total Phenomena</p>
                    <p className="text-2xl font-bold text-yellow-900">{opportunityGaps.summary?.total_phenomena || 0}</p>
                  </div>
                  <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                    <p className="text-sm text-red-600 font-medium mb-1">High Opportunity</p>
                    <p className="text-2xl font-bold text-red-900">{opportunityGaps.summary?.high_opportunity_count || 0}</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                    <p className="text-sm text-green-600 font-medium mb-1">Well-Theorized</p>
                    <p className="text-2xl font-bold text-green-900">{opportunityGaps.summary?.well_theorized_count || 0}</p>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <p className="text-sm text-blue-600 font-medium mb-1">Avg Coverage</p>
                    <p className="text-2xl font-bold text-blue-900">
                      {opportunityGaps.summary?.avg_theory_coverage?.toFixed(1) || '0.0'} theories
                    </p>
                  </div>
                </div>

                {/* High Opportunity Phenomena */}
                {opportunityGaps.high_opportunity && opportunityGaps.high_opportunity.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Research Opportunities</h3>
                    <div className="bg-red-50 rounded-xl p-6 border-2 border-red-200">
                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {opportunityGaps.high_opportunity.map((opp, idx) => (
                          <div key={opp.phenomenon_name} className="bg-white rounded-lg p-4 border border-red-200 hover:shadow-md transition-shadow">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <h4 className="font-semibold text-gray-900 mb-2">{opp.phenomenon_name}</h4>
                                <div className="flex items-center gap-4 text-sm text-gray-600">
                                  <span className="flex items-center gap-1">
                                    <span className="font-medium text-red-600">Opportunity Score:</span>
                                    <span className="font-bold text-red-700">{(opp.opportunity_gap_score * 100).toFixed(0)}%</span>
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <span>Theories:</span>
                                    <span className="font-semibold">{opp.theory_count}</span>
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <span>Papers:</span>
                                    <span className="font-semibold">{opp.paper_count}</span>
                                  </span>
                                </div>
                                {opp.theories && opp.theories.length > 0 && (
                                  <div className="mt-2">
                                    <p className="text-xs text-gray-500 mb-1">Current theories:</p>
                                    <div className="flex flex-wrap gap-1">
                                      {opp.theories.map((theory, tIdx) => (
                                        <span key={tIdx} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                          {theory}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Well-Theorized Phenomena */}
                {opportunityGaps.well_theorized && opportunityGaps.well_theorized.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Well-Theorized Phenomena</h3>
                    <div className="bg-green-50 rounded-xl p-6 border-2 border-green-200">
                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {opportunityGaps.well_theorized.map((opp, idx) => (
                          <div key={opp.phenomenon_name} className="bg-white rounded-lg p-4 border border-green-200 hover:shadow-md transition-shadow">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <h4 className="font-semibold text-gray-900 mb-2">{opp.phenomenon_name}</h4>
                                <div className="flex items-center gap-4 text-sm text-gray-600">
                                  <span className="flex items-center gap-1">
                                    <span>Theories:</span>
                                    <span className="font-semibold text-green-700">{opp.theory_count}</span>
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <span>Papers:</span>
                                    <span className="font-semibold">{opp.paper_count}</span>
                                  </span>
                                </div>
                                {opp.theories && opp.theories.length > 0 && (
                                  <div className="mt-2">
                                    <p className="text-xs text-gray-500 mb-1">Theories:</p>
                                    <div className="flex flex-wrap gap-1">
                                      {opp.theories.map((theory, tIdx) => (
                                        <span key={tIdx} className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                                          {theory}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
        ) : activeTab === 'integration' ? (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-6">
              <Sparkles size={24} className="text-purple-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Integration Mechanism</h2>
                <p className="text-gray-600 mt-1">Theory co-usage patterns and cross-domain integration</p>
              </div>
            </div>

            {integrationMechanism && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                    <p className="text-sm text-purple-600 font-medium mb-1">Avg Integration Score</p>
                    <p className="text-2xl font-bold text-purple-900">
                      {integrationMechanism.summary?.avg_integration_score?.toFixed(2) || '0.00'}
                    </p>
                    <p className="text-xs text-purple-600 mt-1">theories per paper</p>
                  </div>
                  <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
                    <p className="text-sm text-indigo-600 font-medium mb-1">Integration Diversity</p>
                    <p className="text-2xl font-bold text-indigo-900">
                      {integrationMechanism.summary?.avg_integration_diversity?.toFixed(2) || '0.00'}
                    </p>
                    <p className="text-xs text-indigo-600 mt-1">Shannon entropy</p>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <p className="text-sm text-blue-600 font-medium mb-1">Top Integration Pairs</p>
                    <p className="text-2xl font-bold text-blue-900">
                      {integrationMechanism.top_integration_pairs?.length || 0}
                    </p>
                    <p className="text-xs text-blue-600 mt-1">theory combinations</p>
                  </div>
                </div>

                {integrationMechanism.intervals && integrationMechanism.intervals.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Integration Score Over Time</h3>
                    <ResponsiveContainer width="100%" height={350}>
                      <LineChart data={integrationMechanism.intervals}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis 
                          dataKey="interval" 
                          angle={-45} 
                          textAnchor="end" 
                          height={80}
                          tick={{ fill: '#6b7280', fontSize: 11 }}
                        />
                        <YAxis 
                          label={{ value: 'Integration Score', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#6b7280', fontSize: 11 } }}
                          tick={{ fill: '#6b7280', fontSize: 11 }}
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#fff', 
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                            boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                          }}
                        />
                        <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />
                        <Line 
                          type="monotone" 
                          dataKey="integration_score" 
                          stroke="#8B5CF6" 
                          strokeWidth={2} 
                          dot={{ fill: '#8B5CF6', r: 3 }}
                          name="Integration Score"
                        />
                        <Line 
                          type="monotone" 
                          dataKey="integration_diversity" 
                          stroke="#6366F1" 
                          strokeWidth={2} 
                          dot={{ fill: '#6366F1', r: 3 }}
                          name="Integration Diversity"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {integrationMechanism.top_integration_pairs && integrationMechanism.top_integration_pairs.length > 0 && (
                  <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Theory Integration Pairs</h3>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {integrationMechanism.top_integration_pairs.map((pair, idx) => (
                        <div key={`${pair.theory1}-${pair.theory2}`} className="bg-white rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <span className="text-sm font-semibold text-gray-500">#{idx + 1}</span>
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-gray-900">{pair.theory1}</span>
                                <ArrowRight size={16} className="text-gray-400" />
                                <span className="font-semibold text-gray-900">{pair.theory2}</span>
                              </div>
                            </div>
                            <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-semibold">
                              {pair.total_co_usage} papers
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
        ) : activeTab === 'cumulative' ? (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-6">
              <TrendingUp size={24} className="text-green-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Cumulative Theory & Knowledge Accumulation</h2>
                <p className="text-gray-600 mt-1">How theories build on previous work and knowledge accumulates over time</p>
              </div>
            </div>

            {loading && !cumulativeTheory ? (
              <div className="text-center py-12">
                <Loading />
                <p className="text-gray-600 mt-4">Loading cumulative theory data...</p>
              </div>
            ) : !cumulativeTheory ? (
              <div className="text-center py-12">
                <p className="text-gray-600">Cumulative theory data is not available.</p>
                <p className="text-sm text-gray-500 mt-2">This may take a moment to load.</p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                    <p className="text-sm text-green-600 font-medium mb-1">Total Theories</p>
                    <p className="text-2xl font-bold text-green-900">
                      {cumulativeTheory.summary?.total_theories || 0}
                    </p>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <p className="text-sm text-blue-600 font-medium mb-1">Total Connections</p>
                    <p className="text-2xl font-bold text-blue-900">
                      {cumulativeTheory.summary?.total_connections || 0}
                    </p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                    <p className="text-sm text-purple-600 font-medium mb-1">Avg Accumulation Rate</p>
                    <p className="text-2xl font-bold text-purple-900">
                      {cumulativeTheory.summary?.avg_accumulation_rate?.toFixed(2) || '0.00'}
                    </p>
                    <p className="text-xs text-purple-600 mt-1">connections per paper</p>
                  </div>
                  <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                    <p className="text-sm text-orange-600 font-medium mb-1">Avg Persistence</p>
                    <p className="text-2xl font-bold text-orange-900">
                      {(cumulativeTheory.summary?.avg_persistence * 100)?.toFixed(1) || '0.0'}%
                    </p>
                    <p className="text-xs text-orange-600 mt-1">theories remain active</p>
                  </div>
                </div>

                {cumulativeTheory.intervals && cumulativeTheory.intervals.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Knowledge Accumulation Over Time</h3>
                    <ResponsiveContainer width="100%" height={400}>
                      <AreaChart data={cumulativeTheory.intervals}>
                        <defs>
                          <linearGradient id="colorTheories" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10B981" stopOpacity={0.8}/>
                            <stop offset="95%" stopColor="#10B981" stopOpacity={0.1}/>
                          </linearGradient>
                          <linearGradient id="colorConnections" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                            <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis 
                          dataKey="interval" 
                          angle={-45} 
                          textAnchor="end" 
                          height={80}
                          tick={{ fill: '#6b7280', fontSize: 11 }}
                        />
                        <YAxis 
                          label={{ value: 'Cumulative Count', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#6b7280', fontSize: 11 } }}
                          tick={{ fill: '#6b7280', fontSize: 11 }}
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#fff', 
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                            boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                          }}
                        />
                        <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />
                        <Area 
                          type="monotone" 
                          dataKey="cumulative_theories" 
                          stroke="#10B981" 
                          fillOpacity={1} 
                          fill="url(#colorTheories)"
                          name="Cumulative Theories"
                        />
                        <Area 
                          type="monotone" 
                          dataKey="cumulative_connections" 
                          stroke="#3B82F6" 
                          fillOpacity={1} 
                          fill="url(#colorConnections)"
                          name="Cumulative Connections"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {cumulativeTheory.intervals && cumulativeTheory.intervals.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">New Knowledge Per Interval</h3>
                    <ResponsiveContainer width="100%" height={350}>
                      <BarChart data={cumulativeTheory.intervals}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis 
                          dataKey="interval" 
                          angle={-45} 
                          textAnchor="end" 
                          height={80}
                          tick={{ fill: '#6b7280', fontSize: 11 }}
                        />
                        <YAxis 
                          label={{ value: 'New Count', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#6b7280', fontSize: 11 } }}
                          tick={{ fill: '#6b7280', fontSize: 11 }}
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#fff', 
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                            boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                          }}
                        />
                        <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />
                        <Bar dataKey="new_theories" fill="#10B981" radius={[8, 8, 0, 0]} name="New Theories" />
                        <Bar dataKey="new_connections" fill="#3B82F6" radius={[8, 8, 0, 0]} name="New Connections" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
        ) : activeTab === 'canonical' ? (
        <div className="space-y-6">
          {/* Canonical Coverage & Centrality Tab */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-6">
              <Calendar size={24} className="text-blue-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Canonical Problem Analysis</h2>
                <p className="text-gray-600 mt-1">Coverage ratio and centrality metrics for canonical papers</p>
              </div>
            </div>

            {/* Canonical Coverage */}
            {loading && !canonicalCoverage ? (
              <div className="text-center py-12 mb-6">
                <Loading />
                <p className="text-gray-600 mt-4">Loading canonical coverage data...</p>
              </div>
            ) : !canonicalCoverage ? (
              <div className="text-center py-12 mb-6">
                <p className="text-gray-600">Canonical coverage data is not available.</p>
                <p className="text-sm text-gray-500 mt-2">This may take a moment to load.</p>
              </div>
            ) : canonicalCoverage && canonicalCoverage.coverage_by_year && canonicalCoverage.coverage_by_year.length > 0 ? (
              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Canonical Coverage Ratio by Year</h3>
                  {canonicalCoverage.summary?.method && (
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      Method: {canonicalCoverage.summary.method === 'theory_phenomenon_connectivity' 
                        ? `Theory/Phenomenon Connectivity (min: ${canonicalCoverage.summary.min_connections || 5} connections)`
                        : 'Canonical Problem Property'}
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <p className="text-sm text-blue-600 font-medium mb-1">Avg Coverage</p>
                    <p className="text-2xl font-bold text-blue-900">
                      {(canonicalCoverage.summary?.avg_coverage * 100)?.toFixed(1) || '0.0'}%
                    </p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                    <p className="text-sm text-green-600 font-medium mb-1">Total Canonical</p>
                    <p className="text-2xl font-bold text-green-900">
                      {canonicalCoverage.summary?.total_canonical_papers || 0}
                    </p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                    <p className="text-sm text-purple-600 font-medium mb-1">Total Papers</p>
                    <p className="text-2xl font-bold text-purple-900">
                      {canonicalCoverage.summary?.total_papers || 0}
                    </p>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={350}>
                  <LineChart data={canonicalCoverage.coverage_by_year}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      dataKey="year" 
                      tick={{ fill: '#6b7280', fontSize: 11 }}
                    />
                    <YAxis 
                      label={{ value: 'Coverage Ratio', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#6b7280', fontSize: 11 } }}
                      tick={{ fill: '#6b7280', fontSize: 11 }}
                      domain={[0, 1]}
                    />
                    <Tooltip 
                      formatter={(value) => [(value * 100).toFixed(1) + '%', 'Coverage']}
                      contentStyle={{ 
                        backgroundColor: '#fff', 
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                      }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="coverage_ratio" 
                      stroke="#3B82F6" 
                      strokeWidth={2} 
                      dot={{ fill: '#3B82F6', r: 3 }}
                      name="Coverage Ratio"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : canonicalCoverage && canonicalCoverage.coverage_by_year && canonicalCoverage.coverage_by_year.length === 0 ? (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
                <p className="text-yellow-800 font-medium mb-2">⚠️ No Coverage Data Available</p>
                <p className="text-sm text-yellow-700">Papers may not have the `canonical_problem` property set in the database.</p>
              </div>
            ) : null}

            {/* Canonical Centrality */}
            {loading && !canonicalCentrality ? (
              <div className="text-center py-12">
                <Loading />
                <p className="text-gray-600 mt-4">Loading canonical centrality data...</p>
                <p className="text-sm text-gray-500 mt-2">This may take up to 60 seconds (NetworkX calculation)</p>
              </div>
            ) : canonicalCentrality?.error ? (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                <p className="text-yellow-800 font-medium mb-2">⚠️ Centrality Calculation Unavailable</p>
                <p className="text-sm text-yellow-700">{canonicalCentrality.error}</p>
                <p className="text-xs text-yellow-600 mt-2">Note: This requires NetworkX library and paper citation relationships.</p>
              </div>
            ) : canonicalCentrality && !canonicalCentrality.error && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Centrality Comparison: Canonical vs Non-Canonical</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div className="bg-blue-50 rounded-xl p-6 border border-blue-200">
                    <h4 className="font-semibold text-blue-900 mb-4">Canonical Papers</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-blue-700">Avg Eigenvector:</span>
                        <span className="font-bold text-blue-900">
                          {canonicalCentrality.canonical_centrality?.avg_eigenvector?.toFixed(4) || '0.0000'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-blue-700">Avg PageRank:</span>
                        <span className="font-bold text-blue-900">
                          {canonicalCentrality.canonical_centrality?.avg_pagerank?.toFixed(4) || '0.0000'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-blue-700">Paper Count:</span>
                        <span className="font-bold text-blue-900">
                          {canonicalCentrality.canonical_centrality?.paper_count || 0}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                    <h4 className="font-semibold text-gray-900 mb-4">Non-Canonical Papers</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-700">Avg Eigenvector:</span>
                        <span className="font-bold text-gray-900">
                          {canonicalCentrality.non_canonical_centrality?.avg_eigenvector?.toFixed(4) || '0.0000'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-700">Avg PageRank:</span>
                        <span className="font-bold text-gray-900">
                          {canonicalCentrality.non_canonical_centrality?.avg_pagerank?.toFixed(4) || '0.0000'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-700">Paper Count:</span>
                        <span className="font-bold text-gray-900">
                          {canonicalCentrality.non_canonical_centrality?.paper_count || 0}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                {canonicalCentrality.comparison && (
                  <div className="bg-yellow-50 rounded-xl p-6 border border-yellow-200">
                    <h4 className="font-semibold text-yellow-900 mb-4">Comparison Ratios</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-sm text-yellow-700">Eigenvector Ratio:</span>
                        <span className="ml-2 font-bold text-yellow-900">
                          {canonicalCentrality.comparison.eigenvector_ratio?.toFixed(2) || '0.00'}x
                        </span>
                      </div>
                      <div>
                        <span className="text-sm text-yellow-700">PageRank Ratio:</span>
                        <span className="ml-2 font-bold text-yellow-900">
                          {canonicalCentrality.comparison.pagerank_ratio?.toFixed(2) || '0.00'}x
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
            {canonicalCentrality?.error && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800">{canonicalCentrality.error}</p>
              </div>
            )}
          </div>
        </div>
        ) : activeTab === 'hhi' ? (
        <div className="space-y-6">
          {/* HHI Concentration Tab */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-6">
              <BarChart3 size={24} className="text-indigo-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Theoretical Concentration Index (HHI)</h2>
                <p className="text-gray-600 mt-1">Herfindahl-Hirschman Index: High = dominance, Low = fragmentation</p>
              </div>
            </div>

            {theoreticalConcentration && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
                    <p className="text-sm text-indigo-600 font-medium mb-1">Average HHI</p>
                    <p className="text-2xl font-bold text-indigo-900">
                      {theoreticalConcentration.summary?.avg_hhi?.toFixed(3) || '0.000'}
                    </p>
                    <p className="text-xs text-indigo-600 mt-1">
                      {theoreticalConcentration.summary?.avg_hhi > 0.25 ? 'High Concentration' :
                       theoreticalConcentration.summary?.avg_hhi > 0.15 ? 'Moderate' : 'Fragmented'}
                    </p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                    <p className="text-sm text-purple-600 font-medium mb-1">Trend</p>
                    <p className="text-2xl font-bold text-purple-900 capitalize">
                      {theoreticalConcentration.summary?.trend || 'stable'}
                    </p>
                  </div>
                </div>

                {theoreticalConcentration.intervals && theoreticalConcentration.intervals.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">HHI Over Time</h3>
                    <ResponsiveContainer width="100%" height={350}>
                      <LineChart data={theoreticalConcentration.intervals}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis 
                          dataKey="interval" 
                          angle={-45} 
                          textAnchor="end" 
                          height={80}
                          tick={{ fill: '#6b7280', fontSize: 11 }}
                        />
                        <YAxis 
                          label={{ value: 'HHI Index', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#6b7280', fontSize: 11 } }}
                          tick={{ fill: '#6b7280', fontSize: 11 }}
                          domain={[0, 1]}
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#fff', 
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                            boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                          }}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="hhi" 
                          stroke="#6366F1" 
                          strokeWidth={2} 
                          dot={{ fill: '#6366F1', r: 3 }}
                          name="HHI"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Top Theories by Interval */}
                {theoreticalConcentration.intervals && theoreticalConcentration.intervals.length > 0 && (
                  <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Theories by Interval</h3>
                    <div className="space-y-4 max-h-96 overflow-y-auto">
                      {theoreticalConcentration.intervals
                        .filter(interval => interval.top_theories && interval.top_theories.length > 0)
                        .map(interval => (
                          <div key={interval.interval} className="bg-white rounded-lg p-4 border border-gray-200">
                            <div className="flex items-center justify-between mb-3">
                              <h4 className="font-semibold text-gray-900">{interval.interval}</h4>
                              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                interval.interpretation === 'high_concentration' ? 'bg-red-100 text-red-700' :
                                interval.interpretation === 'moderate_concentration' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-green-100 text-green-700'
                              }`}>
                                HHI: {interval.hhi?.toFixed(3)}
                              </span>
                            </div>
                            <ul className="space-y-1">
                              {interval.top_theories.map(([theory, count], idx) => (
                                <li key={theory} className="flex items-center justify-between text-sm">
                                  <span className="flex items-center gap-2">
                                    <span className="text-gray-500">#{idx + 1}</span>
                                    <span className="text-gray-900">{theory}</span>
                                  </span>
                                  <span className="text-gray-600 font-medium">{count} uses</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
        ) : activeTab === 'alignment' ? (
        <div className="space-y-6">
          {/* Theory-Problem Alignment Tab - COMMENTED OUT DUE TO SYNTAX ERRORS */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-6">
              <Target size={24} className="text-green-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Theory-Problem Alignment</h2>
                <p className="text-gray-600 mt-1">This feature is temporarily disabled due to syntax errors.</p>
              </div>
            </div>
            <div className="text-center py-12">
              <p className="text-gray-600">Theory-Problem Alignment feature is currently unavailable.</p>
              <p className="text-sm text-gray-500 mt-2">Please check back later.</p>
            </div>
          </div>
        </div>
        ) : activeTab === 'integrative' ? (
        <div className="space-y-6">
          {/* Integrative Theory Centrality Tab - COMMENTED OUT DUE TO UI ERRORS */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-6">
              <Sparkles size={24} className="text-purple-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Integrative Theory Centrality</h2>
                <p className="text-gray-600 mt-1">This feature is temporarily disabled due to UI errors.</p>
              </div>
            </div>
            <div className="text-center py-12">
              <p className="text-gray-600">Integrative Theory Centrality feature is currently unavailable.</p>
              <p className="text-sm text-gray-500 mt-2">Please check back later.</p>
            </div>
          </div>
        </div>
        ) : activeTab === 'authors' ? (
        <div className="space-y-6">
          {/* Author Counts by Period Tab */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-6">
              <BookOpen size={24} className="text-blue-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Author Counts by Period</h2>
                <p className="text-gray-600 mt-1">Number of unique authors publishing in each 5-year period</p>
              </div>
            </div>

            {/* Summary Cards */}
            {authorCounts.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <BookOpen size={20} />
                    <span className="text-blue-100 text-sm font-medium">Total Authors</span>
                  </div>
                  <p className="text-3xl font-bold">
                    {authorCounts.reduce((sum, interval) => sum + (interval.total_authors || 0), 0).toLocaleString()}
                  </p>
                  <p className="text-blue-100 text-xs mt-1">Across all periods</p>
                </div>
                
                <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white shadow-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp size={20} />
                    <span className="text-purple-100 text-sm font-medium">Avg per Period</span>
                  </div>
                  <p className="text-3xl font-bold">
                    {authorCounts.length > 0 
                      ? Math.round(authorCounts.reduce((sum, interval) => sum + (interval.total_authors || 0), 0) / authorCounts.length)
                      : 0}
                  </p>
                  <p className="text-purple-100 text-xs mt-1">5-year periods</p>
                </div>
                
                <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl p-6 text-white shadow-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Target size={20} />
                    <span className="text-indigo-100 text-sm font-medium">Peak Period</span>
                  </div>
                  <p className="text-3xl font-bold">
                    {authorCounts.length > 0 
                      ? authorCounts.reduce((max, interval) => 
                          (interval.total_authors || 0) > (max.total_authors || 0) ? interval : max, 
                          authorCounts[0]
                        ).interval
                      : 'N/A'}
                  </p>
                  <p className="text-indigo-100 text-xs mt-1">
                    {authorCounts.length > 0 
                      ? `${authorCounts.reduce((max, interval) => 
                          (interval.total_authors || 0) > (max.total_authors || 0) ? interval : max, 
                          authorCounts[0]
                        ).total_authors || 0} authors`
                      : ''}
                  </p>
                </div>
              </div>
            )}

            {/* Author Counts Chart */}
            {authorCounts.length > 0 ? (
              <>
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Author Counts Over Time</h3>
                  <ResponsiveContainer width="100%" height={350}>
                    <BarChart 
                      data={authorCounts.map(interval => ({
                        interval: interval.interval,
                        authors: interval.total_authors || 0,
                        papers: interval.total_papers || 0
                      }))} 
                      margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis 
                        dataKey="interval" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100}
                        tick={{ fill: '#6b7280', fontSize: 11 }}
                      />
                      <YAxis 
                        yAxisId="left"
                        label={{ value: 'Number of Authors', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#6b7280', fontSize: 11 } }}
                        tick={{ fill: '#6b7280', fontSize: 11 }}
                      />
                      <YAxis 
                        yAxisId="right"
                        orientation="right"
                        label={{ value: 'Number of Papers', angle: 90, position: 'insideRight', style: { textAnchor: 'middle', fill: '#8B5CF6', fontSize: 11 } }}
                        tick={{ fill: '#8B5CF6', fontSize: 11 }}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#fff', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                        }}
                      />
                      <Legend wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }} />
                      <Bar 
                        yAxisId="left"
                        dataKey="authors" 
                        fill="#3B82F6" 
                        name="Authors"
                        radius={[6, 6, 0, 0]}
                      />
                      <Bar 
                        yAxisId="right"
                        dataKey="papers" 
                        fill="#8B5CF6" 
                        name="Papers"
                        radius={[6, 6, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Detailed Author List by Period */}
                <div className="mt-6 border-t border-gray-200 pt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Authors by Period</h3>
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {authorCounts.map((interval) => (
                      <div key={interval.interval} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-semibold text-gray-900">{interval.interval}</h4>
                          <span className="text-sm text-gray-600">
                            {interval.total_authors || 0} authors • {interval.total_papers || 0} papers
                          </span>
                        </div>
                        {interval.authors && interval.authors.length > 0 ? (
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                            {interval.authors.slice(0, 20).map((author, idx) => (
                              <div 
                                key={author.author_id || idx} 
                                className="bg-white rounded-lg p-3 border border-gray-200 shadow-sm"
                              >
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-sm font-semibold text-gray-900 truncate" title={author.full_name}>
                                    {author.full_name || `${author.given_name || ''} ${author.family_name || ''}`.trim() || 'Unknown Author'}
                                  </span>
                                  <span className="text-xs text-gray-600 ml-2 flex-shrink-0">
                                    {author.paper_count || 0} paper{author.paper_count !== 1 ? 's' : ''}
                                  </span>
                                </div>
                                {(author.given_name || author.family_name) && (
                                  <div className="text-xs text-gray-500">
                                    {[author.given_name, author.family_name].filter(Boolean).join(' ')}
                                  </div>
                                )}
                              </div>
                            ))}
                            {interval.authors.length > 20 && (
                              <div className="bg-gray-100 rounded-lg p-3 border border-gray-200 text-center">
                                <span className="text-sm text-gray-600">
                                  +{interval.authors.length - 20} more authors
                                </span>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500">No authors found for this period</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-600">No author data available.</p>
                <p className="text-sm text-gray-500 mt-2">Author data will appear here once available.</p>
              </div>
            )}
          </div>
        </div>
        ) : activeTab === 'phenomena' ? (
        <div className="space-y-6">
          {/* Phenomenon Evolution by Period Tab */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-6">
              <Sparkles size={24} className="text-purple-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Phenomenon Evolution by Period</h2>
                <p className="text-gray-600 mt-1">Top 20 phenomena studied in each 5-year period</p>
              </div>
            </div>

            {/* Summary Cards */}
            {phenomenonCounts.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white shadow-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles size={20} />
                    <span className="text-purple-100 text-sm font-medium">Total Phenomena</span>
                  </div>
                  <p className="text-3xl font-bold">
                    {phenomenonCounts.reduce((sum, interval) => sum + (interval.total_phenomena || 0), 0).toLocaleString()}
                  </p>
                  <p className="text-purple-100 text-xs mt-1">Across all periods</p>
                </div>
                
                <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl p-6 text-white shadow-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp size={20} />
                    <span className="text-indigo-100 text-sm font-medium">Avg per Period</span>
                  </div>
                  <p className="text-3xl font-bold">
                    {phenomenonCounts.length > 0 
                      ? Math.round(phenomenonCounts.reduce((sum, interval) => sum + (interval.total_phenomena || 0), 0) / phenomenonCounts.length)
                      : 0}
                  </p>
                  <p className="text-indigo-100 text-xs mt-1">5-year periods</p>
                </div>
                
                <div className="bg-gradient-to-br from-pink-500 to-pink-600 rounded-xl p-6 text-white shadow-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Target size={20} />
                    <span className="text-pink-100 text-sm font-medium">Peak Period</span>
                  </div>
                  <p className="text-3xl font-bold">
                    {phenomenonCounts.length > 0 
                      ? phenomenonCounts.reduce((max, interval) => 
                          (interval.total_phenomena || 0) > (max.total_phenomena || 0) ? interval : max, 
                          phenomenonCounts[0]
                        ).interval
                      : 'N/A'}
                  </p>
                  <p className="text-pink-100 text-xs mt-1">
                    {phenomenonCounts.length > 0 
                      ? `${phenomenonCounts.reduce((max, interval) => 
                          (interval.total_phenomena || 0) > (max.total_phenomena || 0) ? interval : max, 
                          phenomenonCounts[0]
                        ).total_phenomena || 0} phenomena`
                      : ''}
                  </p>
                </div>
              </div>
            )}

            {/* Phenomenon Counts Chart */}
            {phenomenonCounts.length > 0 ? (
              <>
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Phenomenon Counts Over Time</h3>
                  <ResponsiveContainer width="100%" height={350}>
                    <BarChart 
                      data={phenomenonCounts.map(interval => ({
                        interval: interval.interval,
                        phenomena: interval.total_phenomena || interval.total_unique_phenomena || 0,
                        papers: interval.total_papers_in_interval || interval.total_papers || 0
                      }))} 
                      margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis 
                        dataKey="interval" 
                        angle={-45} 
                        textAnchor="end" 
                        height={100}
                        tick={{ fill: '#6b7280', fontSize: 11 }}
                      />
                      <YAxis 
                        yAxisId="left"
                        label={{ value: 'Number of Phenomena', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#6b7280', fontSize: 11 } }}
                        tick={{ fill: '#6b7280', fontSize: 11 }}
                      />
                      <YAxis 
                        yAxisId="right"
                        orientation="right"
                        label={{ value: 'Number of Papers', angle: 90, position: 'insideRight', style: { textAnchor: 'middle', fill: '#8B5CF6', fontSize: 11 } }}
                        tick={{ fill: '#8B5CF6', fontSize: 11 }}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#fff', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                        }}
                      />
                      <Legend wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }} />
                      <Bar 
                        yAxisId="left"
                        dataKey="phenomena" 
                        fill="#8B5CF6" 
                        name="Phenomena"
                        radius={[6, 6, 0, 0]}
                      />
                      <Bar 
                        yAxisId="right"
                        dataKey="papers" 
                        fill="#EC4899" 
                        name="Papers"
                        radius={[6, 6, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Top 20 Phenomena by Period */}
                <div className="mt-6 border-t border-gray-200 pt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Top 20 Phenomena by Period</h3>
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {phenomenonCounts.map((interval) => (
                      <div key={interval.interval} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-semibold text-gray-900">{interval.interval}</h4>
                          <span className="text-sm text-gray-600">
                            {interval.total_phenomena || 0} total phenomena • {interval.top_phenomena_count || 0} shown • {interval.total_papers || 0} papers
                          </span>
                        </div>
                        {interval.top_phenomena && interval.top_phenomena.length > 0 ? (
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                            {interval.top_phenomena.map((phenomenon, idx) => (
                              <div 
                                key={phenomenon.phenomenon_name || idx} 
                                className="bg-white rounded-lg p-3 border border-gray-200 shadow-sm"
                                style={{ borderLeft: `4px solid ${topicColors[idx % topicColors.length]}` }}
                              >
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-sm font-semibold text-gray-900 truncate flex-1" title={phenomenon.phenomenon_name}>
                                    #{idx + 1}. {phenomenon.phenomenon_name || 'Unknown Phenomenon'}
                                  </span>
                                  <span className="text-xs text-gray-600 ml-2 flex-shrink-0">
                                    {phenomenon.paper_count || 0} paper{phenomenon.paper_count !== 1 ? 's' : ''}
                                  </span>
                                </div>
                                {phenomenon.paper_ids && phenomenon.paper_ids.length > 0 && (
                                  <div className="text-xs text-gray-500 mt-1">
                                    {phenomenon.paper_ids.length} paper{phenomenon.paper_ids.length !== 1 ? 's' : ''} studied this
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500">No phenomena found for this period</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-600">No phenomenon data available.</p>
                <p className="text-sm text-gray-500 mt-2">Phenomenon data will appear here once available.</p>
              </div>
            )}
          </div>
        </div>
        ) : null}
      </div>

      {/* Professional Chat Sidebar - Right Side */}
      {chatOpen && (
        <>
          {/* Overlay for mobile */}
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden transition-opacity"
            onClick={() => setChatOpen(false)}
          />
          
          {/* Chat Sidebar - Professional Design */}
          <div className="fixed right-0 top-0 bottom-0 w-full lg:w-[420px] bg-white shadow-2xl z-50 flex flex-col border-l border-gray-200 transition-transform duration-300 ease-in-out">
            {/* Chat Header */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-4 border-b border-blue-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/20 rounded-lg">
                    <MessageCircle size={20} className="text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">Research Assistant</h3>
                    <p className="text-xs text-blue-100">Ask questions about the data</p>
                  </div>
                </div>
                <button
                  onClick={() => setChatOpen(false)}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                  title="Close chat"
                >
                  <X size={20} className="text-white" />
                </button>
              </div>
            </div>

            {/* Chat Interface */}
            <div className="flex-1 overflow-hidden flex flex-col">
              <ChatInterface
                messages={messages}
                onSendMessage={handleSendMessage}
                onClearChat={handleClearChat}
                isLoading={chatLoading}
              />
            </div>
          </div>
        </>
      )}

      {/* Floating Chat Button (when closed) - Professional Design */}
      {!chatOpen && (
        <button
          onClick={() => setChatOpen(true)}
          className="fixed bottom-8 right-8 w-14 h-14 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-full shadow-2xl hover:shadow-3xl transition-all hover:scale-110 flex items-center justify-center z-40 group"
          title="Open Research Assistant"
          aria-label="Open Research Assistant"
        >
          <MessageCircle size={24} className="group-hover:scale-110 transition-transform" />
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full border-2 border-white flex items-center justify-center">
            <span className="text-xs font-bold text-white">?</span>
          </span>
        </button>
      )}
    </div>
  );
};

export default AdvancedAnalyticsDashboard;
