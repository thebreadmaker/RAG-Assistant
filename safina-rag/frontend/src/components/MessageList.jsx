import React from 'react'

function MessageList({ messages, isLoading, onExampleClick }) {
  if (messages.length === 0 && !isLoading) {
    return (
      <div className="messages">
        <div className="empty-state">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
          </svg>
          <h3>Welcome to Safina Assistant</h3>
          <p>Ask about customer eligibility using @retail_digital</p>
          
          <div className="example-queries">
            <div 
              className="example-query"
              onClick={() => onExampleClick('@retail_digital why is customer 599741 excluded?')}
            >
              @retail_digital why is customer 599741 excluded?
            </div>
            <div 
              className="example-query"
              onClick={() => onExampleClick('@retail_digital check eligibility for 503044')}
            >
              @retail_digital check eligibility for 503044
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="messages">
      {messages.map((msg, idx) => (
        <div key={idx} className={`message ${msg.type}`}>
          <div className="message-bubble">
            {msg.type === 'agent' && <strong>Safina Assistant</strong>}
            {msg.content}
          </div>
        </div>
      ))}
      
      {isLoading && (
        <div className="message agent">
          <div className="message-bubble">
            <div className="loading">
              <div className="loading-dot"></div>
              <div className="loading-dot"></div>
              <div className="loading-dot"></div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MessageList