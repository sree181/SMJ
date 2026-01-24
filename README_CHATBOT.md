# SMJ Research Chatbot 🚀

A modern, Google-style web interface for querying Strategic Management Journal research papers with interactive knowledge graph visualization.

## ✨ Features

- **🤖 Intelligent Chat Interface**: Ask natural language questions about research
- **🕸️ Interactive Knowledge Graph**: Visualize connections between papers, concepts, and findings
- **📊 Real-time Analytics**: See research patterns, gaps, and influential papers
- **🎨 Google-style UI**: Clean, intuitive design with modern UX
- **⚡ FastAPI Backend**: High-performance API with automatic documentation
- **🔗 Neo4j Integration**: Connected to your knowledge graph database

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Server │    │   Neo4j Graph   │
│   (Port 3000)   │◄──►│   (Port 5000)   │◄──►│   (Aura Cloud)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Option 1: One-Command Startup
```bash
# Install dependencies and start everything
python start_chatbot.py
```

### Option 2: Manual Setup
```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Node.js dependencies
npm install

# 3. Start FastAPI server (Terminal 1)
python api_server.py

# 4. Start React app (Terminal 2)
npm start
```

## 🌐 Access Points

- **Chatbot Interface**: http://localhost:3000
- **API Documentation**: http://localhost:5000/docs
- **API Health Check**: http://localhost:5000/api/health

## 💬 How to Use

### 1. Ask Questions
Type natural language questions like:
- "What are the main research themes in strategic management?"
- "What methodologies are used in top management research?"
- "How do mergers and acquisitions affect management teams?"
- "What are the research gaps in the field?"

### 2. Explore Knowledge Graph
- Switch to the "Knowledge Graph" tab to see visual connections
- Click on nodes to get detailed information
- Use search to filter specific concepts
- Zoom and pan to explore the graph

### 3. View Research Insights
- Get AI-generated insights based on your questions
- See connected papers and their relationships
- Identify influential research and emerging patterns

## 🔧 Configuration

### Environment Variables
Make sure your `.env` file contains:
```env
NEO4J_URI=neo4j+s://your-aura-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
OPENAI_API_KEY=your-openai-key
```

### API Endpoints

#### `GET /api/health`
Check system health and Neo4j connection status.

#### `POST /api/query`
Process user questions and return answers with graph data.
```json
{
  "query": "What are the main research themes?"
}
```

#### `GET /api/graph`
Get full knowledge graph data for visualization.

#### `GET /api/stats`
Get statistics about the knowledge graph.

## 🎨 UI Components

### Chat Interface
- **Message History**: Scrollable conversation with timestamps
- **Smart Input**: Auto-resizing textarea with keyboard shortcuts
- **Suggestion Chips**: Quick-start questions for new users
- **Loading States**: Visual feedback during processing

### Knowledge Graph
- **Interactive Visualization**: Powered by Cytoscape.js
- **Node Types**: Papers, Questions, Methodologies, Findings, Entities
- **Search & Filter**: Find specific nodes quickly
- **Zoom Controls**: Navigate large graphs easily
- **Legend**: Understand different node types

### Header
- **Connection Status**: Real-time Neo4j connection indicator
- **Refresh Button**: Retry connection if needed
- **Clean Design**: Google-style minimal interface

## 🛠️ Development

### Project Structure
```
src/
├── components/
│   ├── ChatInterface.js      # Main chat component
│   ├── GraphVisualization.js # Knowledge graph component
│   └── Header.js             # App header
├── App.js                    # Main app component
├── App.css                   # App styles
└── index.js                  # React entry point

api_server.py                 # FastAPI backend
start_chatbot.py             # Startup script
```

### Adding New Features

1. **New API Endpoints**: Add to `api_server.py`
2. **UI Components**: Create in `src/components/`
3. **Graph Layouts**: Modify Cytoscape configuration
4. **Styling**: Update CSS files

### Customization

- **Colors**: Modify CSS variables in component files
- **Graph Layout**: Change layout algorithm in `GraphVisualization.js`
- **LLM Model**: Update model in `api_server.py`
- **Node Styles**: Customize Cytoscape stylesheet

## 🔍 Troubleshooting

### Common Issues

1. **"Connection Error"**
   - Check Neo4j credentials in `.env`
   - Verify Neo4j Aura instance is running
   - Check network connectivity

2. **"Failed to get response"**
   - Verify OpenAI API key is set
   - Check API server logs
   - Ensure server is running on port 5000

3. **Graph not loading**
   - Check if data exists in Neo4j
   - Verify graph query in `api_server.py`
   - Check browser console for errors

4. **React app won't start**
   - Run `npm install` to install dependencies
   - Check Node.js version (requires 14+)
   - Clear npm cache: `npm cache clean --force`

### Debug Mode
```bash
# Start with debug logging
DEBUG=1 python api_server.py

# Check API health
curl http://localhost:5000/api/health

# Test query endpoint
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test question"}'
```

## 📊 Performance

- **FastAPI**: Async processing, ~100ms response times
- **React**: Virtual DOM, optimized re-renders
- **Cytoscape**: Hardware-accelerated graph rendering
- **Neo4j**: Indexed queries, connection pooling

## 🔒 Security

- **CORS**: Configured for localhost development
- **Input Validation**: Pydantic models for API requests
- **Error Handling**: Graceful degradation on failures
- **Environment Variables**: Secure credential management

## 🚀 Production Deployment

### Build for Production
```bash
# Build React app
npm run build

# Serve with production server
pip install gunicorn
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker Deployment
```dockerfile
FROM node:18-alpine as frontend
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY src/ src/
COPY public/ public/
RUN npm run build

FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY api_server.py .
COPY --from=frontend /app/build ./build
EXPOSE 5000
CMD ["python", "api_server.py"]
```

## 📈 Future Enhancements

- **Real-time Updates**: WebSocket connections for live data
- **Advanced Analytics**: More sophisticated graph algorithms
- **Export Features**: PDF reports, graph exports
- **User Authentication**: Multi-user support
- **Mobile App**: React Native version
- **Voice Interface**: Speech-to-text integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the Strategic Management Journal research initiative.

---

**Built with ❤️ for Strategic Management Research**
