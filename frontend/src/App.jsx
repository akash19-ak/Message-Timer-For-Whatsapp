import { useState, useEffect, useCallback } from 'react'
import BirthdayForm from './components/BirthdayForm'
import ScheduledList from './components/ScheduledList'
import NotificationAlert from './components/NotificationAlert'
import DarkModeToggle from './components/DarkModeToggle'
import { useSchedules } from './hooks/useSchedules'

export default function App() {
  const [dark, setDark] = useState(() => {
    try { return localStorage.getItem('bwa-theme') === 'dark' } catch { return false }
  })
  const [submitting, setSubmitting] = useState(false)
  const [notification, setNotification] = useState(null)

  const { schedules, loading, error, fetchSchedules, createSchedule, deleteSchedule, updateSchedule, sendNow } = useSchedules()

  // Apply dark mode
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
    try { localStorage.setItem('bwa-theme', dark ? 'dark' : 'light') } catch {}
  }, [dark])

  // Auto-dismiss notifications
  useEffect(() => {
    if (!notification) return
    const t = setTimeout(() => setNotification(null), 5000)
    return () => clearTimeout(t)
  }, [notification])

  const handleSubmit = useCallback(async (formData) => {
    setSubmitting(true)
    try {
      const created = await createSchedule(formData)
      setNotification({
        type: 'success',
        message: `🎉 Birthday wish for ${created.name} scheduled successfully!`,
      })
    } finally {
      setSubmitting(false)
    }
  }, [createSchedule])

  const handleSendNow = useCallback(async (id, name) => {
    try {
      const result = await sendNow(id)
      setNotification({
        type: 'success',
        message: `📱 WhatsApp Web is opening for ${name}! Message will auto-send in ~25 seconds. Make sure you are logged in to WhatsApp Web!`,
      })
      return result
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.response?.data?.error || 'Failed to open WhatsApp. Make sure the backend is running.',
      })
    }
  }, [sendNow])

  const handleDelete = useCallback(async (id) => {
    await deleteSchedule(id)
    setNotification({ type: 'success', message: '🗑️ Wish deleted.' })
  }, [deleteSchedule])

  const handleUpdate = useCallback(async (id, payload) => {
    await updateSchedule(id, payload)
    setNotification({ type: 'success', message: '✏️ Wish updated successfully!' })
  }, [updateSchedule])

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="app-logo">
          <div className="app-logo-icon">🎂</div>
          <div>
            <h1>Birthday Wish Assistant</h1>
            <p>Automate WhatsApp birthday greetings</p>
          </div>
        </div>
        <DarkModeToggle dark={dark} onToggle={() => setDark(d => !d)} />
      </header>

      {/* Notification */}
      <NotificationAlert notification={notification} onClose={() => setNotification(null)} />

      {/* Main content */}
      <main className="main-grid">
        <aside>
          <BirthdayForm onSubmit={handleSubmit} loading={submitting} />
        </aside>

        <section>
        <ScheduledList
            schedules={schedules}
            loading={loading}
            error={error}
            onDelete={handleDelete}
            onUpdate={handleUpdate}
            onSendNow={handleSendNow}
            onRefresh={fetchSchedules}
          />
        </section>
      </main>
    </div>
  )
}
