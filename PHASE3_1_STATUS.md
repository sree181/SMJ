# Phase 3.1: Research Trajectory & Trend Forecasting - IN PROGRESS

## ✅ Backend Implementation Complete

### Endpoint: `GET /api/trends/{entity_type}/{entity_name}`

**Features**:
- ✅ Normalizes entity names using EntityNormalizer
- ✅ Queries usage by time period (from TimePeriod nodes or paper relationships)
- ✅ Calculates evolution steps between consecutive periods
- ✅ Generates trend forecast for next period
- ✅ Generates LLM narrative ("where field has been", "where it's going")
- ✅ Generates LLM summary

**Response Structure**:
```json
{
  "entity_type": "theory",
  "entity_name": "Resource-Based View",
  "usage_by_period": [
    {
      "period": "2020-2024",
      "start_year": 2020,
      "end_year": 2024,
      "paper_count": 15,
      "usage_frequency": 3.0
    }
  ],
  "evolution_steps": [
    {
      "from_period": "2015-2019",
      "to_period": "2020-2024",
      "change": 5,
      "change_percentage": 50.0,
      "evolution_type": "increasing"
    }
  ],
  "forecast": {
    "next_period": "2025-2029",
    "predicted_paper_count": 20,
    "confidence": 0.8,
    "trend_direction": "increasing",
    "rationale": "..."
  },
  "narrative": "LLM-generated...",
  "summary": "LLM-generated..."
}
```

---

## ⏳ Frontend Implementation - TODO

### Components Needed:
1. **TrendsDashboard.js** - Main screen for trend analysis
2. **TrendChart.js** - Timeline visualization component
3. **EvolutionSteps.js** - Display evolution between periods
4. **ForecastCard.js** - Display forecast information

### API Service:
- Add `api.getTrendAnalysis(entityType, entityName)` method

### Routing:
- Add route `/trends/:entityType/:entityName`
- Update Dashboard to link to trends

---

## 🚀 Next Steps

1. Create frontend components
2. Add API service method
3. Add routing
4. Test end-to-end


