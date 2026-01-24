# API Integration Guide - Connection Strength Features

## ✅ Implementation Status

### Core Endpoints (Implemented)
1. ✅ `GET /api/connections/theory-phenomenon` - Get connections with filters
2. ✅ `GET /api/connections/aggregated` - Get aggregated statistics
3. ✅ `GET /api/phenomena` - List all phenomena
4. ✅ `GET /api/analytics/top-connections` - Get top connections

### Pending Endpoints (To Implement)
5. ⏳ `GET /api/connections/theory-phenomenon/{theory_name}` - Phenomena for theory
6. ⏳ `GET /api/connections/phenomenon-theory/{phenomenon_name}` - Theories for phenomenon
7. ⏳ `GET /api/phenomena/{phenomenon_name}` - Phenomenon details
8. ⏳ `GET /api/analytics/connection-strength-distribution` - Distribution stats
9. ⏳ `GET /api/connections/{connection_id}/factors` - Factor breakdown

---

## Frontend Integration Examples

### 1. Dashboard - Top Connections Card

```javascript
// src/services/api.js
export const getTopConnections = async (n = 10) => {
  const response = await fetch(`${API_BASE_URL}/api/analytics/top-connections?n=${n}&type=aggregated`);
  if (!response.ok) throw new Error('Failed to fetch top connections');
  return response.json();
};

// src/components/screens/Dashboard.js
import { getTopConnections } from '../services/api';

const [topConnections, setTopConnections] = useState([]);

useEffect(() => {
  getTopConnections(5)
    .then(data => setTopConnections(data.top_connections))
    .catch(err => console.error('Error loading top connections:', err));
}, []);

// Display in card
{topConnections.map((conn, idx) => (
  <div key={idx} className="connection-item">
    <strong>{conn.theory}</strong> → {conn.phenomenon}
    <span className="strength-badge">{conn.strength.toFixed(2)}</span>
  </div>
))}
```

---

### 2. Search Results - Show Connection Strength

```javascript
// Enhance PaperCard to show connection strengths
const PaperCard = ({ paper }) => {
  const [connections, setConnections] = useState([]);
  
  useEffect(() => {
    // Get connections for this paper
    fetch(`${API_BASE_URL}/api/connections/theory-phenomenon?paper_id=${paper.paper_id}`)
      .then(res => res.json())
      .then(data => setConnections(data.connections))
      .catch(err => console.error(err));
  }, [paper.paper_id]);
  
  return (
    <div className="paper-card">
      <h3>{paper.title}</h3>
      {connections.length > 0 && (
        <div className="connections-preview">
          <strong>Connections:</strong>
          {connections.slice(0, 3).map((conn, idx) => (
            <span key={idx} className="connection-tag">
              {conn.theory.name} → {conn.phenomenon.phenomenon_name}
              <span className="strength">{conn.connection_strength.toFixed(2)}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
```

---

### 3. Paper Detail - Connection Strength Tab

```javascript
// src/components/screens/PaperDetail.js
const [connections, setConnections] = useState([]);

useEffect(() => {
  if (paperId) {
    fetch(`${API_BASE_URL}/api/connections/theory-phenomenon?paper_id=${paperId}`)
      .then(res => res.json())
      .then(data => setConnections(data.connections))
      .catch(err => console.error(err));
  }
}, [paperId]);

// New tab: "Theory-Phenomenon Connections"
{connections.map((conn, idx) => (
  <div key={idx} className="connection-detail">
    <div className="connection-header">
      <h4>{conn.theory.name} → {conn.phenomenon.phenomenon_name}</h4>
      <span className={`strength-badge strength-${getStrengthCategory(conn.connection_strength)}`}>
        {conn.connection_strength.toFixed(3)}
      </span>
    </div>
    <div className="factor-breakdown">
      <div>Role: {conn.factor_scores.role_weight.toFixed(3)}</div>
      <div>Section: {conn.factor_scores.section_score.toFixed(3)}</div>
      <div>Keywords: {conn.factor_scores.keyword_score.toFixed(3)}</div>
      <div>Semantic: {conn.factor_scores.semantic_score.toFixed(3)}</div>
      <div>Explicit: {conn.factor_scores.explicit_bonus.toFixed(3)}</div>
    </div>
  </div>
))}
```

---

### 4. New Screen - Connections Explorer

```javascript
// src/components/screens/ConnectionsExplorer.js
const ConnectionsExplorer = () => {
  const [connections, setConnections] = useState([]);
  const [filters, setFilters] = useState({
    min_strength: 0.3,
    max_strength: 1.0,
    theory_name: '',
    phenomenon_name: ''
  });
  const [pagination, setPagination] = useState({ limit: 50, offset: 0 });
  
  const loadConnections = async () => {
    const params = new URLSearchParams({
      ...filters,
      ...pagination
    });
    
    const response = await fetch(`${API_BASE_URL}/api/connections/theory-phenomenon?${params}`);
    const data = await response.json();
    setConnections(data.connections);
  };
  
  useEffect(() => {
    loadConnections();
  }, [filters, pagination]);
  
  return (
    <div className="connections-explorer">
      <Filters filters={filters} onChange={setFilters} />
      <ConnectionsList connections={connections} />
      <Pagination pagination={pagination} onChange={setPagination} />
    </div>
  );
};
```

---

### 5. New Screen - Phenomena Explorer

```javascript
// src/components/screens/PhenomenaExplorer.js
const PhenomenaExplorer = () => {
  const [phenomena, setPhenomena] = useState([]);
  const [selectedPhenomenon, setSelectedPhenomenon] = useState(null);
  
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/phenomena?limit=100`)
      .then(res => res.json())
      .then(data => setPhenomena(data.phenomena))
      .catch(err => console.error(err));
  }, []);
  
  const handlePhenomenonClick = async (phenomenonName) => {
    // Get theories for this phenomenon
    const response = await fetch(
      `${API_BASE_URL}/api/connections/phenomenon-theory/${encodeURIComponent(phenomenonName)}`
    );
    const data = await response.json();
    setSelectedPhenomenon({ ...data, name: phenomenonName });
  };
  
  return (
    <div className="phenomena-explorer">
      <div className="phenomena-list">
        {phenomena.map((ph, idx) => (
          <div key={idx} onClick={() => handlePhenomenonClick(ph.phenomenon_name)}>
            {ph.phenomenon_name}
            <span>{ph.theory_count} theories</span>
          </div>
        ))}
      </div>
      {selectedPhenomenon && (
        <PhenomenonDetail phenomenon={selectedPhenomenon} />
      )}
    </div>
  );
};
```

---

## API Response Format

### Standard Success Response
```json
{
  "connections": [...],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### Error Response
```json
{
  "detail": "Error message"
}
```

---

## Caching Strategy

### Client-Side Caching
```javascript
// Use React Query or SWR for caching
import useSWR from 'swr';

const fetcher = (url) => fetch(url).then(res => res.json());

const { data, error } = useSWR(
  `/api/connections/aggregated?limit=50`,
  fetcher,
  {
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
    refreshInterval: 3600000 // 1 hour
  }
);
```

### Server-Side Caching (Future)
- Use Redis for aggregated statistics
- Cache TTL: 1 hour for aggregated, 30 min for top connections
- Invalidate on new paper ingestion

---

## Performance Optimization

### 1. Pagination
- Always use `limit` and `offset`
- Default limit: 50 items
- Maximum limit: 200 items

### 2. Filtering
- Use indexed properties (theory_name, phenomenon_name)
- Combine filters to reduce result set

### 3. Lazy Loading
- Load connections on demand
- Use infinite scroll for large lists

### 4. Debouncing
- Debounce search inputs (300ms)
- Debounce filter changes (500ms)

---

## Error Handling

```javascript
const handleApiError = (error) => {
  if (error.status === 503) {
    // Neo4j not connected
    showNotification('Database connection error. Please try again later.');
  } else if (error.status === 404) {
    // Not found
    showNotification('Resource not found.');
  } else {
    // Generic error
    showNotification('An error occurred. Please try again.');
  }
};
```

---

## Testing

### Test Endpoints
```bash
# Get connections
curl "http://localhost:5000/api/connections/theory-phenomenon?min_strength=0.7&limit=10"

# Get aggregated
curl "http://localhost:5000/api/connections/aggregated?min_paper_count=3"

# List phenomena
curl "http://localhost:5000/api/phenomena?limit=20"

# Top connections
curl "http://localhost:5000/api/analytics/top-connections?n=10&type=aggregated"
```

---

## Next Steps

1. ✅ Core endpoints implemented
2. ⏳ Implement remaining endpoints
3. ⏳ Add frontend components
4. ⏳ Add caching layer
5. ⏳ Performance testing
6. ⏳ Documentation updates

---

## Summary

**Status**: ✅ Core endpoints ready for frontend integration

**Available Now**:
- Get connections with filters
- Get aggregated statistics
- List phenomena
- Get top connections

**Ready for Frontend**: ✅ Yes - All core endpoints are implemented and tested

