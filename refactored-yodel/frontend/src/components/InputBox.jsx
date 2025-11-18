import React, { useState, useRef } from 'react'

const DEPARTMENTS = [
  { tag: '@retail_digital', name: 'Retail Digital Lending' }
]

function InputBox({ onSend, disabled }) {
  const [input, setInput] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const inputRef = useRef(null)

  const handleInputChange = (e) => {
    const value = e.target.value
    setInput(value)

    // Detect @ symbol for tag suggestions
    const lastAtIndex = value.lastIndexOf('@')
    if (lastAtIndex !== -1) {
      const afterAt = value.slice(lastAtIndex + 1).toLowerCase()
      
      const filtered = DEPARTMENTS.filter(dept =>
        dept.tag.toLowerCase().includes(`@${afterAt}`)
      )
      
      setSuggestions(filtered)
    } else {
      setSuggestions([])
    }
  }

  const handleTagSelect = (tag) => {
    // Replace the @... portion with the selected tag
    const lastAtIndex = input.lastIndexOf('@')
    const beforeAt = input.slice(0, lastAtIndex)
    setInput(beforeAt + tag + ' ')
    setSuggestions([])
    inputRef.current?.focus()
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (input.trim() && !disabled) {
      onSend(input.trim())
      setInput('')
      setSuggestions([])
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="input-container">
      <div className="input-wrapper">
        {suggestions.length > 0 && (
          <div className="tag-suggestions">
            {suggestions.map((dept, idx) => (
              <div
                key={idx}
                className="tag-option"
                onClick={() => handleTagSelect(dept.tag)}
              >
                <div className="tag">{dept.tag}</div>
                <div className="desc">{dept.name}</div>
              </div>
            ))}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="input-form">
          <div className="input-box-container">
            <input
              ref={inputRef}
              type="text"
              className="input-box"
              placeholder="How can I help you today?"
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              disabled={disabled}
              autoFocus
            />
            
            <div className="input-controls">
              <button
                type="submit"
                className="send-button"
                disabled={disabled || !input.trim()}
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M8 2L8 14M8 2L12 6M8 2L4 6" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

export default InputBox