import React, { useState } from 'react'

function formatDateTime(iso) {
  const d = new Date(iso)
  return d.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  })
}

function buildWaLink(phone, message) {
  const clean = phone.replace('+', '').replace(/\s/g, '').replace(/-/g, '')
  return `https://wa.me/${clean}?text=${encodeURIComponent(message)}`
}

function getMinDateTimeLocal() {
  const d = new Date(Date.now() + 60000)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function toLocalInputValue(iso) {
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ─── Edit Modal ──────────────────────────────────────────────────────────────
function EditModal({ schedule, onSave, onClose, saving }) {
  const [form, setForm] = useState({
    name: schedule.name,
    phone: schedule.phone,
    message: schedule.message,
    scheduled_datetime: toLocalInputValue(schedule.scheduled_datetime),
  })
  const [err, setErr] = useState({})

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
    if (err[name]) setErr(prev => ({ ...prev, [name]: null }))
  }

  const handleSave = async (e) => {
    e.preventDefault()
    const errors = {}
    if (!form.name.trim()) errors.name = 'Name is required.'
    if (!form.phone.trim()) errors.phone = 'Phone is required.'
    if (!form.scheduled_datetime) errors.scheduled_datetime = 'Date/time is required.'
    else if (new Date(form.scheduled_datetime) <= new Date()) errors.scheduled_datetime = 'Must be in the future.'
    if (!form.message.trim()) errors.message = 'Message is required.'
    if (Object.keys(errors).length) { setErr(errors); return }
    await onSave({ ...form, scheduled_datetime: new Date(form.scheduled_datetime).toISOString() })
  }

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h3 className="modal-title">✏️ Edit Scheduled Wish</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={handleSave}>
          {[
            { id: 'edit-name', name: 'name', label: '👤 Name', type: 'text', placeholder: 'Recipient name' },
            { id: 'edit-phone', name: 'phone', label: '📱 Phone', type: 'tel', placeholder: '+919876543210' },
          ].map(({ id, name, label, type, placeholder }) => (
            <div className="form-group" key={name}>
              <label htmlFor={id} className="form-label">{label}</label>
              <input id={id} name={name} type={type} className={`form-input${err[name] ? ' error' : ''}`}
                placeholder={placeholder} value={form[name]} onChange={handleChange} />
              {err[name] && <p className="form-error">⚠ {err[name]}</p>}
            </div>
          ))}
          <div className="form-group">
            <label htmlFor="edit-datetime" className="form-label">📅 Date & Time</label>
            <input id="edit-datetime" name="scheduled_datetime" type="datetime-local"
              className={`form-input${err.scheduled_datetime ? ' error' : ''}`}
              min={getMinDateTimeLocal()} value={form.scheduled_datetime} onChange={handleChange} />
            {err.scheduled_datetime && <p className="form-error">⚠ {err.scheduled_datetime}</p>}
          </div>
          <div className="form-group">
            <label htmlFor="edit-message" className="form-label">💬 Message</label>
            <textarea id="edit-message" name="message" className={`form-textarea${err.message ? ' error' : ''}`}
              value={form.message} onChange={handleChange} rows={4} />
            {err.message && <p className="form-error">⚠ {err.message}</p>}
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button id="save-edit-btn" type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving…' : '💾 Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─── Schedule Item ────────────────────────────────────────────────────────────
function ScheduleItem({ schedule, onDelete, onUpdate, onSendNow }) {
  const [deleting, setDeleting] = useState(false)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [sending, setSending] = useState(false)

  const handleDelete = async () => {
    if (!window.confirm(`Delete wish for ${schedule.name}?`)) return
    setDeleting(true)
    try { await onDelete(schedule.id) }
    catch { setDeleting(false) }
  }

  const handleSave = async (payload) => {
    setSaving(true)
    try {
      await onUpdate(schedule.id, payload)
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  const handleSend = async () => {
    setSending(true)
    try { await onSendNow(schedule.id, schedule.name) }
    finally { setSending(false) }
  }

  return (
    <>
      <div className={`schedule-item${schedule.sent ? ' sent' : ''}`}>
        <div className="schedule-item-header">
          <div>
            <div className="schedule-item-name">
              🎁 {schedule.name}
              {schedule.sent
                ? <span className="badge-sent">✅ Sent</span>
                : <span className="badge-pending">⏰ Pending</span>
              }
            </div>
          </div>
          <div className="schedule-item-actions">
            {!schedule.sent && (
              <button
                id={`send-now-btn-${schedule.id}`}
                className="btn"
                style={{
                  background: 'linear-gradient(135deg, #25d366, #128c7e)',
                  color: '#fff',
                  padding: '0.4rem 0.85rem',
                  fontSize: '0.8rem',
                  borderRadius: 'var(--radius-sm)',
                  border: 'none',
                  gap: '0.35rem',
                  boxShadow: '0 2px 8px rgba(37,211,102,0.3)',
                  opacity: sending ? 0.7 : 1,
                  cursor: sending ? 'not-allowed' : 'pointer',
                }}
                onClick={handleSend}
                disabled={sending}
                title="Open WhatsApp Web and send this message now"
              >
                {sending ? '⏳ Opening…' : '📱 Send Now'}
              </button>
            )}
            <a
              href={buildWaLink(schedule.phone, schedule.message)}
              target="_blank"
              rel="noopener noreferrer"
              className="wa-test-link"
              title="Open wa.me link manually"
            >
              <span>🔗</span> Link
            </a>
            {!schedule.sent && (
              <button
                id={`edit-btn-${schedule.id}`}
                className="btn btn-edit"
                onClick={() => setEditing(true)}
                title="Edit"
              >✏️</button>
            )}
            <button
              id={`delete-btn-${schedule.id}`}
              className="btn btn-danger"
              onClick={handleDelete}
              disabled={deleting}
              title="Delete"
            >{deleting ? '…' : '🗑'}</button>
          </div>
        </div>

        <div className="schedule-meta">
          <span className="meta-chip">📅 {formatDateTime(schedule.scheduled_datetime)}</span>
          <span className="meta-chip phone">📱 {schedule.phone}</span>
        </div>

        <div className="schedule-message">
          {schedule.message}
        </div>
      </div>

      {editing && (
        <EditModal
          schedule={schedule}
          onSave={handleSave}
          onClose={() => setEditing(false)}
          saving={saving}
        />
      )}
    </>
  )
}

// ─── Scheduled List ───────────────────────────────────────────────────────────
export default function ScheduledList({ schedules, loading, error, onDelete, onUpdate, onSendNow, onRefresh }) {
  const pending = schedules.filter(s => !s.sent)
  const sent = schedules.filter(s => s.sent)

  if (loading) {
    return (
      <div className="card">
        <h2 className="card-title"><span className="icon">📋</span> Scheduled Wishes</h2>
        <div className="loader"><div className="spinner" /></div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="section-header">
        <h2 className="section-title">
          <span>📋</span> Scheduled Wishes
        </h2>
        <button id="refresh-btn" className="btn btn-ghost" onClick={onRefresh} style={{ padding: '0.4rem 0.85rem', fontSize: '0.82rem' }}>
          🔄 Refresh
        </button>
      </div>

      {/* Stats bar */}
      <div className="stats-bar">
        <div className="stat-chip">⏳ Pending <span className="val">{pending.length}</span></div>
        <div className="stat-chip">✅ Sent <span className="val">{sent.length}</span></div>
        <div className="stat-chip">📊 Total <span className="val">{schedules.length}</span></div>
      </div>

      {/* How it works notice */}
      <div style={{
        background: 'rgba(37,211,102,0.08)',
        border: '1px solid rgba(37,211,102,0.2)',
        borderRadius: 'var(--radius-sm)',
        padding: '0.65rem 1rem',
        fontSize: '0.8rem',
        color: 'var(--text-secondary)',
        marginBottom: '1rem',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.5rem',
      }}>
        <span>📱</span>
        <span>
          <strong>How it works:</strong> Click <strong>"Send Now"</strong> to open WhatsApp Web with the message pre-filled. WhatsApp Web will load and the message will be auto-sent after ~20 seconds. Make sure you are logged in to WhatsApp Web first!
        </span>
      </div>

      {error && (
        <div className="notification error" style={{ marginBottom: '1rem' }}>
          <span className="notification-icon">❌</span>
          <span className="notification-text">{error}</span>
        </div>
      )}

      {schedules.length === 0 ? (
        <div className="empty-state">
          <span className="empty-state-icon">🎈</span>
          <h3>No wishes scheduled yet</h3>
          <p>Fill in the form on the left to schedule your first birthday wish!</p>
        </div>
      ) : (
        <>
          {pending.length > 0 && (
            <>
              <p style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-muted)', marginBottom: '0.6rem' }}>
                ⏳ Upcoming
              </p>
              <div className="schedule-list" style={{ marginBottom: '1.5rem' }}>
                {pending.map(s => (
                  <ScheduleItem key={s.id} schedule={s} onDelete={onDelete} onUpdate={onUpdate} onSendNow={onSendNow} />
                ))}
              </div>
            </>
          )}
          {sent.length > 0 && (
            <>
              <p style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--text-muted)', marginBottom: '0.6rem' }}>
                ✅ Already Sent
              </p>
              <div className="schedule-list">
                {sent.map(s => (
                  <ScheduleItem key={s.id} schedule={s} onDelete={onDelete} onUpdate={onUpdate} onSendNow={onSendNow} />
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
