import { useState, useRef, useEffect } from 'react'
import MessageList from './MessageList'
import InputBox from './InputBox'

function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (query) => {
    // Add user message
    const userMessage = {
      type: 'user',
      content: query,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const response = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()

      // Add agent response
      const agentMessage = {
        type: 'agent',
        content: data.answer,
        metadata: data.metadata,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, agentMessage])
    } catch (error) {
      const errorMessage = {
        type: 'agent',
        content: `Error: ${error.message}. Please ensure the backend is running.`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleExampleClick = (query) => {
    handleSendMessage(query)
  }

  return (
    <>
      <MessageList 
        messages={messages} 
        isLoading={isLoading}
        onExampleClick={handleExampleClick}
      />
      <div ref={messagesEndRef} />
      <InputBox 
        onSend={handleSendMessage} 
        disabled={isLoading}
      />
    </>
  )
}

export default ChatInterface