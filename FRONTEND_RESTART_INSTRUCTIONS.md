# Frontend Restart Instructions

## Issue
You're seeing the old frontend even after new components were added.

## Solution

### Option 1: Hard Refresh Browser
1. **Chrome/Edge**: Press `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. **Firefox**: Press `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac)
3. **Safari**: Press `Cmd+Option+R`

This clears the browser cache and reloads the latest version.

---

### Option 2: Restart Frontend Server

**If frontend is running**:
1. Stop the current server (Ctrl+C in the terminal)
2. Clear build cache:
   ```bash
   cd "Strategic Management Journal"
   rm -rf node_modules/.cache
   ```
3. Restart:
   ```bash
   npm start
   ```

**If frontend is not running**:
```bash
cd "Strategic Management Journal"
npm start
```

---

### Option 3: Clear All Caches

```bash
cd "Strategic Management Journal"

# Clear npm cache
npm cache clean --force

# Clear React build cache
rm -rf node_modules/.cache
rm -rf build

# Reinstall dependencies (if needed)
npm install

# Start fresh
npm start
```

---

## Verify New Components

### Check if files exist:
```bash
ls -la src/components/common/PersonaSelector.js
ls -la src/components/screens/MetricsDashboard.js
ls -la src/components/common/MetricsCard.js
```

### Check if routes are updated:
```bash
grep -n "MetricsDashboard\|PersonaSelector" src/App.js
```

---

## New Features to Test

### 1. Metrics Dashboard
- Navigate to: `http://localhost:3000/metrics/theory`
- Should show search bar and metrics interface

### 2. Persona Selector
- Navigate to: `http://localhost:3000/query`
- Should show persona selector cards below search bar
- Select different personas and query

---

## Troubleshooting

### If still seeing old UI:

1. **Check browser console** (F12):
   - Look for errors
   - Check if components are loading

2. **Check terminal output**:
   - Look for compilation errors
   - Check if webpack compiled successfully

3. **Verify file changes**:
   ```bash
   # Check if App.js has new routes
   grep "MetricsDashboard" src/App.js
   
   # Check if QueryResults has PersonaSelector
   grep "PersonaSelector" src/components/screens/QueryResults.js
   ```

4. **Clear browser data**:
   - Open DevTools (F12)
   - Right-click refresh button
   - Select "Empty Cache and Hard Reload"

---

## Expected Behavior After Restart

### Metrics Dashboard (`/metrics/theory`)
- Search bar at top
- Persona selector (if applicable)
- Metrics cards grid
- LLM narrative summary

### Query Results (`/query`)
- Search bar at top
- **Persona selector with 5 cards** (NEW)
- Query display with persona badge
- LLM answer
- Source papers

---

## Quick Test

1. Open: `http://localhost:3000/query`
2. You should see **5 persona cards** below the search bar
3. If you don't see them, the frontend hasn't reloaded

---

**The frontend server is restarting. Wait 10-15 seconds, then hard refresh your browser (Cmd+Shift+R or Ctrl+Shift+R).**

