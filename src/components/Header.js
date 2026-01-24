import React from 'react';
import { RefreshCw, Wifi, WifiOff, AlertCircle } from 'lucide-react';
import './Header.css';

const Header = ({ connectionStatus, onRefreshConnection }) => {
  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <Wifi className="status-icon connected" />;
      case 'error':
        return <WifiOff className="status-icon error" />;
      case 'connecting':
        return <RefreshCw className="status-icon connecting" />;
      default:
        return <AlertCircle className="status-icon error" />;
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected to Knowledge Graph';
      case 'error':
        return 'Connection Error';
      case 'connecting':
        return 'Connecting...';
      default:
        return 'Unknown Status';
    }
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <h1 className="header-title">
            📚 SMJ Research Chatbot
          </h1>
          <p className="header-subtitle">
            Ask questions about Strategic Management research
          </p>
        </div>
        
        <div className="header-right">
          <div className="status-indicator">
            {getStatusIcon()}
            <span className="status-text">{getStatusText()}</span>
          </div>
          
          {connectionStatus === 'error' && (
            <button 
              className="refresh-button"
              onClick={onRefreshConnection}
              title="Retry Connection"
            >
              <RefreshCw size={16} />
            </button>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
