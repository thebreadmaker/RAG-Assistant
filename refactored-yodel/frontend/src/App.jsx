import React from 'react'
import ChatInterface from './components/ChatInterface'
import ThemeToggle from './components/ThemeToggle'

function App() {
  return (
    <div className="app">
      <header className="header">
        <h1>🏦 Personal Assistant</h1>
        <ThemeToggle />
      </header>
      <ChatInterface />
    </div>
  )
}

export default App