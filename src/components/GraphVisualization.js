import React, { useEffect, useRef, useState } from 'react';
import { Network, Search, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import './GraphVisualization.css';

// Create a fallback graph component
const FallbackGraph = ({ elements }) => (
  <div className="fallback-graph">
    <div className="fallback-content">
      <Network size={48} />
      <h3>Knowledge Graph</h3>
      <p>Interactive graph visualization</p>
      <div className="node-list">
        {elements?.nodes?.slice(0, 5).map((node, index) => (
          <div key={index} className="node-item">
            <div className="node-dot"></div>
            <span>{node.data?.label || node.id}</span>
          </div>
        ))}
      </div>
    </div>
  </div>
);

// Use only the fallback component for now
const CytoscapeComponent = FallbackGraph;

const GraphVisualization = ({ data, onNodeClick }) => {
  const cyRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredData, setFilteredData] = useState(data);

  useEffect(() => {
    if (data) {
      setFilteredData(data);
    }
  }, [data]);

  useEffect(() => {
    if (data && searchTerm) {
      const filtered = {
        nodes: data.nodes.filter(node => 
          node.data.label?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          node.id.toLowerCase().includes(searchTerm.toLowerCase())
        ),
        edges: data.edges.filter(edge => {
          const source = data.nodes.find(n => n.id === edge.data.source);
          const target = data.nodes.find(n => n.id === edge.data.target);
          return (source?.data.label?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                  target?.data.label?.toLowerCase().includes(searchTerm.toLowerCase()));
        })
      };
      setFilteredData(filtered);
    } else if (data) {
      setFilteredData(data);
    }
  }, [searchTerm, data]);

  const layout = {
    name: 'grid',
    animate: true,
    animationDuration: 1000,
    rows: 3,
    cols: 3,
    spacingFactor: 1.5
  };

  const stylesheet = [
    {
      selector: 'node',
      style: {
        'background-color': '#1a73e8',
        'label': 'data(label)',
        'text-valign': 'center',
        'text-halign': 'center',
        'color': 'white',
        'font-size': '12px',
        'font-weight': '500',
        'text-outline-width': 2,
        'text-outline-color': '#1a73e8',
        'width': '60px',
        'height': '60px',
        'border-width': 2,
        'border-color': '#1557b0',
        'border-opacity': 0.8
      }
    },
    {
      selector: 'node:selected',
      style: {
        'background-color': '#ea4335',
        'border-color': '#d33b2c',
        'border-width': 3
      }
    },
    {
      selector: 'node[type="paper"]',
      style: {
        'background-color': '#34a853',
        'border-color': '#2d8f47',
        'shape': 'rectangle',
        'width': '80px',
        'height': '40px'
      }
    },
    {
      selector: 'node[type="question"]',
      style: {
        'background-color': '#fbbc04',
        'border-color': '#f9ab00',
        'color': '#202124',
        'text-outline-color': '#fbbc04'
      }
    },
    {
      selector: 'node[type="methodology"]',
      style: {
        'background-color': '#9c27b0',
        'border-color': '#7b1fa2'
      }
    },
    {
      selector: 'node[type="finding"]',
      style: {
        'background-color': '#ff9800',
        'border-color': '#f57c00',
        'color': '#202124',
        'text-outline-color': '#ff9800'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 2,
        'line-color': '#5f6368',
        'target-arrow-color': '#5f6368',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'opacity': 0.8
      }
    },
    {
      selector: 'edge:selected',
      style: {
        'line-color': '#ea4335',
        'target-arrow-color': '#ea4335',
        'width': 3
      }
    }
  ];

  const handleNodeClick = (event) => {
    const node = event.target;
    setSelectedNode(node);
    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  const handleZoomIn = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 1.2);
    }
  };

  const handleZoomOut = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 0.8);
    }
  };

  const handleReset = () => {
    if (cyRef.current) {
      cyRef.current.fit();
    }
  };

  const handleFit = () => {
    if (cyRef.current) {
      cyRef.current.fit();
    }
  };

  if (!filteredData || !filteredData.nodes || filteredData.nodes.length === 0) {
    return (
      <div className="graph-placeholder">
        <Network size={48} />
        <h3>No Graph Data Available</h3>
        <p>Ask a question to see the knowledge graph visualization</p>
      </div>
    );
  }

  return (
    <div className="graph-container">
      <div className="graph-toolbar">
        <div className="search-container">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search nodes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
        
        <div className="toolbar-buttons">
          <button onClick={handleZoomIn} title="Zoom In">
            <ZoomIn size={16} />
          </button>
          <button onClick={handleZoomOut} title="Zoom Out">
            <ZoomOut size={16} />
          </button>
          <button onClick={handleReset} title="Reset View">
            <RotateCcw size={16} />
          </button>
          <button onClick={handleFit} title="Fit to Screen">
            <Network size={16} />
          </button>
        </div>
      </div>

      <div className="graph-content">
        <CytoscapeComponent elements={filteredData} />
      </div>

      {selectedNode && (
        <div className="node-info">
          <h4>Node Information</h4>
          <div className="node-details">
            <div><strong>ID:</strong> {selectedNode.id()}</div>
            <div><strong>Label:</strong> {selectedNode.data('label') || 'N/A'}</div>
            <div><strong>Type:</strong> {selectedNode.data('type') || 'N/A'}</div>
            {selectedNode.data('year') && (
              <div><strong>Year:</strong> {selectedNode.data('year')}</div>
            )}
            {selectedNode.data('centrality') && (
              <div><strong>Centrality:</strong> {selectedNode.data('centrality').toFixed(3)}</div>
            )}
          </div>
          <button 
            className="close-info"
            onClick={() => setSelectedNode(null)}
          >
            ×
          </button>
        </div>
      )}

      <div className="graph-legend">
        <div className="legend-title">Legend</div>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-color paper"></div>
            <span>Papers</span>
          </div>
          <div className="legend-item">
            <div className="legend-color question"></div>
            <span>Research Questions</span>
          </div>
          <div className="legend-item">
            <div className="legend-color methodology"></div>
            <span>Methodologies</span>
          </div>
          <div className="legend-item">
            <div className="legend-color finding"></div>
            <span>Findings</span>
          </div>
          <div className="legend-item">
            <div className="legend-color entity"></div>
            <span>Entities</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GraphVisualization;
