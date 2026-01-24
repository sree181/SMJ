# UI Implementation Guide - React Components

## 🏗️ Component Structure

```
src/
├── App.js                    # Main app container
├── App.css
├── components/
│   ├── common/
│   │   ├── SearchBar.js      # Main search component
│   │   ├── StatsCard.js      # Stat display card
│   │   ├── PaperCard.js      # Paper preview card
│   │   ├── Button.js         # Reusable button
│   │   └── Loading.js        # Loading spinner
│   ├── layout/
│   │   ├── Header.js         # Top navigation
│   │   ├── Sidebar.js        # Side navigation (desktop)
│   │   └── Footer.js         # Footer
│   ├── screens/
│   │   ├── Dashboard.js      # Home screen
│   │   ├── SearchScreen.js   # Search & results
│   │   ├── PaperDetail.js    # Paper detail view
│   │   ├── TemporalEvolution.js  # Temporal analysis
│   │   ├── GraphExplorer.js  # Graph visualization
│   │   └── Analytics.js      # Analytics dashboard
│   ├── charts/
│   │   ├── TemporalChart.js  # Line/bar charts
│   │   ├── TheoryChart.js    # Theory distribution
│   │   └── MethodChart.js    # Method distribution
│   └── graph/
│       ├── GraphView.js      # Main graph component
│       └── NodeDetails.js    # Node info panel
└── services/
    ├── api.js                # API client
    └── cache.js              # Client-side caching
```

---

## 🎨 Key Components

### 1. SearchBar Component

```jsx
// components/common/SearchBar.js
import React, { useState } from 'react';

const SearchBar = ({ onSearch, placeholder = "Search papers, theories, methods..." }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="search-bar">
      <div className="search-input-wrapper">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="search-input"
        />
        <button type="submit" className="search-button">
          🔍
        </button>
      </div>
      {suggestions.length > 0 && (
        <div className="suggestions-dropdown">
          {suggestions.map((suggestion, i) => (
            <div key={i} onClick={() => onSearch(suggestion)}>
              {suggestion}
            </div>
          ))}
        </div>
      )}
    </form>
  );
};
```

**Styling** (Tailwind CSS):
```css
.search-bar {
  @apply w-full max-w-2xl mx-auto;
}

.search-input-wrapper {
  @apply flex items-center bg-white rounded-lg shadow-md border border-gray-200;
}

.search-input {
  @apply flex-1 px-4 py-3 text-lg outline-none rounded-l-lg;
}

.search-button {
  @apply px-6 py-3 bg-blue-600 text-white rounded-r-lg hover:bg-blue-700;
}
```

---

### 2. PaperCard Component

```jsx
// components/common/PaperCard.js
const PaperCard = ({ paper, onClick }) => {
  return (
    <div 
      className="paper-card"
      onClick={() => onClick(paper)}
    >
      <div className="paper-header">
        <h3 className="paper-title">{paper.title}</h3>
        <span className="paper-year">{paper.year}</span>
      </div>
      
      <div className="paper-authors">
        {paper.authors?.slice(0, 3).map((author, i) => (
          <span key={i} className="author-tag">{author}</span>
        ))}
        {paper.authors?.length > 3 && (
          <span className="more-authors">+{paper.authors.length - 3} more</span>
        )}
      </div>
      
      <p className="paper-abstract">{paper.abstract?.substring(0, 200)}...</p>
      
      <div className="paper-tags">
        {paper.theories?.slice(0, 2).map((theory, i) => (
          <span key={i} className="theory-tag">{theory}</span>
        ))}
        {paper.methods?.slice(0, 2).map((method, i) => (
          <span key={i} className="method-tag">{method}</span>
        ))}
      </div>
      
      <div className="paper-actions">
        <button className="action-btn">View Details</button>
        <button className="action-btn">View Graph</button>
      </div>
    </div>
  );
};
```

**Styling**:
```css
.paper-card {
  @apply bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer;
}

.paper-title {
  @apply text-xl font-semibold text-gray-900 mb-2;
}

.paper-year {
  @apply text-sm text-gray-500;
}

.paper-abstract {
  @apply text-gray-600 text-sm mb-4 line-clamp-3;
}

.theory-tag {
  @apply inline-block px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs mr-2;
}

.method-tag {
  @apply inline-block px-2 py-1 bg-green-100 text-green-800 rounded text-xs mr-2;
}
```

---

### 3. TemporalEvolution Component

```jsx
// components/screens/TemporalEvolution.js
import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const TemporalEvolution = () => {
  const [selectedPeriod, setSelectedPeriod] = useState('2020-2024');
  const [selectedEntity, setSelectedEntity] = useState('theory');
  const [data, setData] = useState([]);

  const periods = ['2020-2024', '2015-2019', '2010-2014', '2005-2009'];

  // Fetch data from API
  useEffect(() => {
    fetch(`/api/temporal/evolution?entity=${selectedEntity}&period=${selectedPeriod}`)
      .then(res => res.json())
      .then(data => setData(data));
  }, [selectedPeriod, selectedEntity]);

  return (
    <div className="temporal-evolution">
      <div className="period-selector">
        {periods.map(period => (
          <button
            key={period}
            className={`period-btn ${selectedPeriod === period ? 'active' : ''}`}
            onClick={() => setSelectedPeriod(period)}
          >
            {period}
          </button>
        ))}
      </div>

      <div className="chart-container">
        <LineChart width={800} height={400} data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="count" stroke="#2563eb" />
        </LineChart>
      </div>

      <div className="trends-section">
        <h3>Emerging Trends</h3>
        <div className="trend-list">
          {/* Display emerging/declining trends */}
        </div>
      </div>
    </div>
  );
};
```

---

### 4. GraphExplorer Component

```jsx
// components/graph/GraphView.js
import React, { useEffect, useRef } from 'react';
import Cytoscape from 'cytoscape';
import cola from 'cytoscape-cola';

Cytoscape.use(cola);

const GraphView = ({ data, onNodeClick }) => {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !data) return;

    cyRef.current = Cytoscape({
      container: containerRef.current,
      elements: data,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'width': 30,
            'height': 30,
            'background-color': 'data(color)',
            'text-valign': 'center',
            'text-halign': 'center'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#ccc',
            'target-arrow-color': '#ccc',
            'target-arrow-shape': 'triangle'
          }
        }
      ],
      layout: {
        name: 'cola',
        nodeSpacing: 50,
        edgeLength: 100
      }
    });

    cyRef.current.on('tap', 'node', (evt) => {
      onNodeClick(evt.target.data());
    });

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [data, onNodeClick]);

  return (
    <div className="graph-container">
      <div className="graph-controls">
        <button onClick={() => cyRef.current?.fit()}>Fit</button>
        <button onClick={() => cyRef.current?.reset()}>Reset</button>
      </div>
      <div ref={containerRef} className="graph-canvas" />
    </div>
  );
};
```

---

## 🎯 Screen Implementations

### Dashboard Screen

```jsx
// components/screens/Dashboard.js
import SearchBar from '../common/SearchBar';
import StatsCard from '../common/StatsCard';

const Dashboard = () => {
  const [stats, setStats] = useState({
    papers: 0,
    theories: 0,
    methods: 0,
    authors: 0
  });

  useEffect(() => {
    fetch('/api/stats')
      .then(res => res.json())
      .then(data => setStats(data));
  }, []);

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Research Assistant</h1>
        <p>Explore Strategic Management Journal research</p>
      </div>

      <div className="search-section">
        <SearchBar onSearch={(query) => navigate(`/search?q=${query}`)} />
      </div>

      <div className="stats-grid">
        <StatsCard label="Papers" value={stats.papers} icon="📄" />
        <StatsCard label="Theories" value={stats.theories} icon="💡" />
        <StatsCard label="Methods" value={stats.methods} icon="🔬" />
        <StatsCard label="Authors" value={stats.authors} icon="👥" />
      </div>

      <div className="quick-actions">
        <button onClick={() => navigate('/temporal')}>
          ⏱️ Temporal Evolution
        </button>
        <button onClick={() => navigate('/graph')}>
          🕸️ Graph Explorer
        </button>
        <button onClick={() => navigate('/analytics')}>
          📊 Analytics
        </button>
      </div>
    </div>
  );
};
```

---

## 🔌 API Integration

### API Service

```jsx
// services/api.js
const API_BASE = 'http://localhost:5000/api';

export const api = {
  // Search
  search: async (query, filters = {}) => {
    const response = await fetch(`${API_BASE}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, ...filters })
    });
    return response.json();
  },

  // Get paper details
  getPaper: async (paperId) => {
    const response = await fetch(`${API_BASE}/papers/${paperId}`);
    return response.json();
  },

  // Temporal evolution
  getTemporalEvolution: async (entityType, period) => {
    const response = await fetch(
      `${API_BASE}/temporal/evolution?entity=${entityType}&period=${period}`
    );
    return response.json();
  },

  // Graph data
  getGraphData: async (paperId) => {
    const response = await fetch(`${API_BASE}/graph/${paperId}`);
    return response.json();
  },

  // Stats
  getStats: async () => {
    const response = await fetch(`${API_BASE}/stats`);
    return response.json();
  }
};
```

---

## 🎨 Styling Approach

### Option 1: Tailwind CSS (Recommended)

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**tailwind.config.js**:
```js
module.exports = {
  content: ['./src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',
        secondary: '#10b981',
        accent: '#f59e0b'
      }
    }
  }
};
```

### Option 2: CSS Modules

```css
/* components/Dashboard.module.css */
.dashboard {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.statsGrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}
```

---

## 📱 Responsive Design

### Mobile-First Breakpoints

```css
/* Mobile: < 640px (default) */
.container {
  padding: 1rem;
}

/* Tablet: ≥ 640px */
@media (min-width: 640px) {
  .container {
    padding: 2rem;
  }
}

/* Desktop: ≥ 1024px */
@media (min-width: 1024px) {
  .container {
    max-width: 1200px;
    margin: 0 auto;
  }
}
```

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
npm install react react-dom react-router-dom
npm install -D tailwindcss postcss autoprefixer
npm install recharts cytoscape cytoscape-cola
npm install axios
```

### 2. Setup Routing

```jsx
// App.js
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './components/screens/Dashboard';
import SearchScreen from './components/screens/SearchScreen';
import PaperDetail from './components/screens/PaperDetail';
import TemporalEvolution from './components/screens/TemporalEvolution';
import GraphExplorer from './components/graph/GraphView';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/search" element={<SearchScreen />} />
        <Route path="/paper/:id" element={<PaperDetail />} />
        <Route path="/temporal" element={<TemporalEvolution />} />
        <Route path="/graph" element={<GraphExplorer />} />
      </Routes>
    </BrowserRouter>
  );
}
```

### 3. Create Base Components

Start with:
1. SearchBar
2. PaperCard
3. StatsCard
4. Dashboard screen

Then build out:
5. SearchScreen
6. PaperDetail
7. TemporalEvolution
8. GraphExplorer

---

## 🎯 Implementation Checklist

### Phase 1: Foundation
- [ ] Setup React Router
- [ ] Install Tailwind CSS
- [ ] Create base layout (Header, Footer)
- [ ] Implement SearchBar component
- [ ] Create Dashboard screen

### Phase 2: Core Features
- [ ] PaperCard component
- [ ] SearchScreen with results
- [ ] PaperDetail screen
- [ ] API integration

### Phase 3: Advanced Features
- [ ] TemporalEvolution screen
- [ ] GraphExplorer component
- [ ] Charts (Recharts)
- [ ] Analytics dashboard

### Phase 4: Polish
- [ ] Responsive design
- [ ] Loading states
- [ ] Error handling
- [ ] Animations
- [ ] Accessibility

---

## 💡 Pro Tips

1. **Start Simple**: Build Dashboard first, then add features
2. **Component Reuse**: Create reusable components (Button, Card, etc.)
3. **State Management**: Use React Context or Zustand for global state
4. **Error Boundaries**: Add error boundaries for better UX
5. **Loading States**: Show loading spinners for async operations
6. **Optimistic UI**: Update UI immediately, sync with server later

---

This guide provides a practical roadmap for implementing the UI design!

