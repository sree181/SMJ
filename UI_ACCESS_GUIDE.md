# How to Access New Features in the UI

## 🎯 New Features Available

### 1. Theory Comparison
**Location**: `/theories/compare`

**How to Access**:
- **From Dashboard**: Click on "Theory Comparison" card (NEW - added to dashboard)
- **Direct URL**: `http://localhost:3000/theories/compare`

**What You Can Do**:
1. Select 2-5 theories to compare
2. View compatibility scores
3. See tensions between theories
4. Get integration suggestions
5. Click "View Full Context →" on any theory card to see detailed analysis

---

### 2. Theory Detail View (NEW - Phase 2.1)
**Location**: `/theories/{theory_name}`

**How to Access**:
- **From Theory Comparison**: After comparing theories, click "View Full Context →" button on any theory card
- **Direct URL**: `http://localhost:3000/theories/Resource-Based%20View`

**What You Can See**:
- **Overview Tab**: Stats, co-usage theories
- **Phenomena Tab**: All phenomena explained by the theory
- **Methods Tab**: Methods typically used with the theory
- **Papers Tab**: Papers using the theory (clickable)
- **Temporal Tab**: Usage over time with bar chart
- **Assumptions Tab**: LLM-generated assumptions analysis
- **Constructs Tab**: Constructs breakdown + LLM narrative

---

## 🔄 If You're Not Seeing New Features

### Step 1: Hard Refresh Browser
**Chrome/Edge**: `Cmd + Shift + R` (Mac) or `Ctrl + Shift + R` (Windows)  
**Firefox**: `Cmd + Shift + R` (Mac) or `Ctrl + Shift + R` (Windows)  
**Safari**: `Cmd + Option + R`

### Step 2: Check Frontend is Running
```bash
# Check if frontend is running
ps aux | grep "npm start" | grep -v grep

# If not running, start it:
cd "Strategic Management Journal"
npm start
```

### Step 3: Clear Browser Cache
1. Open browser DevTools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"

### Step 4: Verify Routes
- Dashboard: `http://localhost:3000/`
- Theory Comparison: `http://localhost:3000/theories/compare`
- Theory Detail: `http://localhost:3000/theories/Resource-Based%20View`

---

## 📍 Quick Access Guide

### From Dashboard:
1. **Theory Comparison Card** (NEW) → Click to compare theories
2. **Query Interface** → Ask questions with personas
3. **Stats Cards** → Click to search

### From Theory Comparison:
1. **Select Theories** → Choose 2-5 theories
2. **Click "Compare Theories"** → View compatibility, tensions, integration
3. **Click "View Full Context →"** → See detailed theory analysis (NEW)

### From Theory Detail:
1. **Browse Tabs** → Overview, Phenomena, Methods, Papers, Temporal, Assumptions, Constructs
2. **Click Papers** → Navigate to paper detail
3. **View Temporal Chart** → See usage over time
4. **Read Narratives** → LLM-generated assumptions and constructs analysis

---

## 🎨 Visual Indicators

**New Features Have**:
- ✅ "Theory Comparison" card on Dashboard (indigo gradient)
- ✅ "View Full Context →" button on theory cards (indigo button)
- ✅ Tabbed interface in Theory Detail view
- ✅ Temporal usage bar chart
- ✅ LLM-generated narratives

---

## 🧪 Test the New Features

### Test Theory Comparison:
1. Go to Dashboard
2. Click "Theory Comparison" card
3. Select "Resource-Based View" and "Dynamic Capabilities Theory"
4. Click "Compare Theories"
5. View compatibility score, tensions, integration suggestions

### Test Theory Detail:
1. After comparing theories, click "View Full Context →" on any theory
2. Explore all 7 tabs
3. Check temporal usage chart
4. Read assumptions and constructs narratives

---

## 🐛 Troubleshooting

**If features don't appear**:
1. ✅ Hard refresh browser (Cmd+Shift+R)
2. ✅ Check frontend is running (`npm start`)
3. ✅ Check backend is running (`python3 api_server.py`)
4. ✅ Clear browser cache
5. ✅ Check browser console for errors (F12)

**If "View Full Context" button doesn't work**:
- Make sure you've run a comparison first
- The button only appears after comparing theories
- Check browser console for navigation errors

---

**All new features are accessible from the Dashboard via the "Theory Comparison" card!**

