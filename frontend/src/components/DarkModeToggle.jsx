import React from 'react'

export default function DarkModeToggle({ dark, onToggle }) {
  return (
    <button
      className="dark-mode-toggle"
      onClick={onToggle}
      aria-label="Toggle dark mode"
      title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {dark ? '☀️' : '🌙'}
      <span>{dark ? 'Light' : 'Dark'}</span>
    </button>
  )
}
