import React from 'react'

export default function NotificationAlert({ notification, onClose }) {
  if (!notification) return null

  return (
    <div className={`notification ${notification.type}`} role="alert">
      <span className="notification-icon">
        {notification.type === 'success' ? '✅' : '❌'}
      </span>
      <span className="notification-text">{notification.message}</span>
      <button className="notification-close" onClick={onClose} aria-label="Close">✕</button>
    </div>
  )
}
