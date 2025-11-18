import React, { useState, useEffect } from 'react'
import { Copy, ThumbsUp, ThumbsDown } from 'lucide-react'

function MessageList({ messages, isLoading, onExampleClick }) {
  const [greetingIndex, setGreetingIndex] = useState(0)
  const [ctaIndex, setCtaIndex] = useState(0)

  // List of 5 greetings
  const greetings = [
    "Welcome to your Personal Assistant",
    "Hello! Your Personal Assistant is ready",
    "Good to see you! Let's get started",
    "Your Personal Assistant at your service",
    "Ready to help with your queries"
  ]

  // List of 5 CTAs
  const ctas = [
    "Ask me anything to get started",
    "What would you like to know today?",
    "How can I assist you?",
    "Start by asking a question",
    "What can I help you with?"
  ]

  // Randomly select greeting and CTA on mount
  useEffect(() => {
    setGreetingIndex(Math.floor(Math.random() * greetings.length))
    setCtaIndex(Math.floor(Math.random() * ctas.length))
  }, [])

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text)
  }

  // Function to format text content with proper HTML structure
  const formatContent = (text) => {
    // Split into lines
    const lines = text.split('\n')
    let html = ''
    let inList = false
    let listType = null
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()
      
      if (!line) {
        if (inList) {
          html += listType === 'ul' ? '</ul>' : '</ol>'
          inList = false
          listType = null
        }
        html += '<br />'
        continue
      }
      
      // Check for unordered list items (-, *, •)
      if (/^[-*•]\s+/.test(line)) {
        if (!inList || listType !== 'ul') {
          if (inList) html += listType === 'ul' ? '</ul>' : '</ol>'
          html += '<ul>'
          inList = true
          listType = 'ul'
        }
        html += `<li>${line.replace(/^[-*•]\s+/, '')}</li>`
        continue
      }
      
      // Check for ordered list items (1., 2., etc)
      if (/^\d+\.\s+/.test(line)) {
        if (!inList || listType !== 'ol') {
          if (inList) html += listType === 'ul' ? '</ul>' : '</ol>'
          html += '<ol>'
          inList = true
          listType = 'ol'
        }
        html += `<li>${line.replace(/^\d+\.\s+/, '')}</li>`
        continue
      }
      
      // Regular paragraph
      if (inList) {
        html += listType === 'ul' ? '</ul>' : '</ol>'
        inList = false
        listType = null
      }
      
      // Check for headers
      if (line.startsWith('### ')) {
        html += `<h3>${line.replace('### ', '')}</h3>`
      } else if (line.startsWith('## ')) {
        html += `<h2>${line.replace('## ', '')}</h2>`
      } else if (line.startsWith('# ')) {
        html += `<h1>${line.replace('# ', '')}</h1>`
      } else {
        html += `<p>${line}</p>`
      }
    }
    
    // Close any open list
    if (inList) {
      html += listType === 'ul' ? '</ul>' : '</ol>'
    }
    
    // Handle inline formatting
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>') // Bold
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>') // Italic
    html = html.replace(/`(.+?)`/g, '<code>$1</code>') // Inline code
    
    return html
  }

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="messages">
        <div className="empty-state">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
          </svg>
          <h3>{greetings[greetingIndex]}</h3>
          <p>{ctas[ctaIndex]}</p>
          
          <div className="example-queries">
            <div 
              className="example-query"
              onClick={() => onExampleClick('@retail_digital why is customer 599741 excluded?')}
            >
              @retail_digital why is customer 599741 excluded?
            </div>
            <div 
              className="example-query"
              onClick={() => onExampleClick('@retail_digital Tell me about the digital personal loan')}
            >
              @retail_digital Tell me about the digital personal loan
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="messages">
      <div className="messages-inner">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.type}`}>
            {msg.type === 'user' ? (
              <>
                <div className="user-avatar">MS</div>
                <div className="message-bubble">{msg.content}</div>
              </>
            ) : (
              <>
                <div 
                  className="message-content"
                  dangerouslySetInnerHTML={{ __html: formatContent(msg.content) }}
                />
                <div className="message-actions">
                  <div className="action-buttons">
                    <button 
                      className="action-button"
                      onClick={() => handleCopy(msg.content)}
                      title="Copy"
                    >
                      <Copy size={18} />
                    </button>
                    <button className="action-button" title="Good response">
                      <ThumbsUp size={18} />
                    </button>
                    <button className="action-button" title="Bad response">
                      <ThumbsDown size={18} />
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        ))}
        
        {isLoading && (
          <div className="message agent">
            <div className="loading">
              <div className="loading-dot"></div>
              <div className="loading-dot"></div>
              <div className="loading-dot"></div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default MessageList