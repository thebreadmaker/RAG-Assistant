import React from 'react'
import ChatInterface from './components/ChatInterface'

function App() {
  return (
    <div className="app">
      <header className="header">
        <h1>🏦 NCBA Safina Digital Lending Assistant</h1>
        <p>Check customer eligibility and get instant answers</p>
      </header>
      <ChatInterface />
    </div>
  )
}

export default App