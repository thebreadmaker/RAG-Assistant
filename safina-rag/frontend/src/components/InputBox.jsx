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
      <form onSubmit={handleSubmit} className="input-wrapper">
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
        
        <input
          ref={inputRef}
          type="text"
          className="input-box"
          placeholder="Type @retail_digital then your question..."
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          autoFocus
        />
        
        <button
          type="submit"
          className="send-button"
          disabled={disabled || !input.trim()}
        >
          Send
        </button>
      </form>
    </div>
  )
}

export default InputBox