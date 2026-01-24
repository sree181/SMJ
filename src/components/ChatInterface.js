import React, { useState, useRef, useEffect } from 'react';
import { Send, Trash2, Bot, User, Loader2 } from 'lucide-react';
import './ChatInterface.css';

const ChatInterface = ({ messages, onSendMessage, onClearChat, isLoading }) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatMessage = (content) => {
    // Simple markdown-like formatting
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="chat-title">
          <Bot size={20} />
          <span>Research Assistant</span>
        </div>
        <button 
          className="clear-button"
          onClick={onClearChat}
          title="Clear conversation"
        >
          <Trash2 size={16} />
        </button>
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <div className="welcome-icon">🤖</div>
            <h3>Welcome to SMJ Research Chatbot</h3>
            <p>Ask me anything about Strategic Management research!</p>
            <div className="suggestions">
              <div className="suggestion-title">Try asking:</div>
              <div className="suggestion-chips">
                <button 
                  className="suggestion-chip"
                  onClick={() => onSendMessage("What are the main research themes in strategic management?")}
                >
                  What are the main research themes?
                </button>
                <button 
                  className="suggestion-chip"
                  onClick={() => onSendMessage("What methodologies are used in top management research?")}
                >
                  What methodologies are used?
                </button>
                <button 
                  className="suggestion-chip"
                  onClick={() => onSendMessage("How do mergers and acquisitions affect management teams?")}
                >
                  How do M&A affect management teams?
                </button>
                <button 
                  className="suggestion-chip"
                  onClick={() => onSendMessage("What are the research gaps in the field?")}
                >
                  What are the research gaps?
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="messages-list">
            {messages.map((message) => (
              <div 
                key={message.id} 
                className={`message ${message.type} ${message.isError ? 'error' : ''}`}
              >
                <div className="message-avatar">
                  {message.type === 'user' ? <User size={16} /> : <Bot size={16} />}
                </div>
                <div className="message-content">
                  <div className="message-text">
                    {message.type === 'bot' ? (
                      <div 
                        dangerouslySetInnerHTML={{ 
                          __html: formatMessage(message.content) 
                        }} 
                      />
                    ) : (
                      message.content
                    )}
                  </div>
                  <div className="message-time">
                    {formatTime(message.timestamp)}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="message bot loading">
                <div className="message-avatar">
                  <Bot size={16} />
                </div>
                <div className="message-content">
                  <div className="loading-indicator">
                    <Loader2 size={16} className="spinning" />
                    <span>Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <form className="input-form" onSubmit={handleSubmit}>
        <div className="input-container">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about Strategic Management research..."
            className="message-input"
            rows="1"
            disabled={isLoading}
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={!inputValue.trim() || isLoading}
          >
            <Send size={16} />
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface;
