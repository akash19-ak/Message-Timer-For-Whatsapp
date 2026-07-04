import React, { useState, useRef } from 'react'
import TemplateSelector from './TemplateSelector'

const PHONE_REGEX = /^\+?[1-9]\d{6,14}$/
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/jpg']
const MAX_SIZE_MB = 10

function getMinDateTime() {
  const d = new Date(Date.now() + 60000)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const INITIAL_STATE = {
  name: '',
  phone: '',
  scheduled_datetime: '',
  message: '',
}

export default function BirthdayForm({ onSubmit, loading }) {
  const [form, setForm] = useState(INITIAL_STATE)
  const [errors, setErrors] = useState({})
  const [activeTemplate, setActiveTemplate] = useState(null)
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const fileInputRef = useRef(null)

  const validate = () => {
    const e = {}
    if (!form.name.trim()) e.name = 'Name is required.'
    if (!form.phone.trim()) {
      e.phone = 'Phone number is required.'
    } else if (!PHONE_REGEX.test(form.phone.replace(/\s/g, ''))) {
      e.phone = 'Enter a valid phone number with country code (e.g. +919876543210).'
    }
    if (!form.scheduled_datetime) {
      e.scheduled_datetime = 'Please select a date and time.'
    } else if (new Date(form.scheduled_datetime) <= new Date()) {
      e.scheduled_datetime = 'Scheduled time must be in the future.'
    }
    if (!form.message.trim()) e.message = 'Message cannot be empty.'
    else if (form.message.trim().length < 10) e.message = 'Message must be at least 10 characters.'
    return e
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: null }))
  }

  const handleTemplateSelect = (text) => {
    setForm(prev => ({ ...prev, message: text }))
    if (errors.message) setErrors(prev => ({ ...prev, message: null }))
  }

  const handleImageChange = (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (!ALLOWED_TYPES.includes(file.type)) {
      setErrors(prev => ({ ...prev, image: 'Only JPG, PNG, or GIF images are allowed.' }))
      return
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setErrors(prev => ({ ...prev, image: `Image must be smaller than ${MAX_SIZE_MB}MB.` }))
      return
    }
    setImageFile(file)
    setImagePreview(URL.createObjectURL(file))
    setErrors(prev => ({ ...prev, image: null }))
  }

  const handleRemoveImage = () => {
    setImageFile(null)
    setImagePreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const validationErrors = validate()
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    const isoDatetime = new Date(form.scheduled_datetime).toISOString()

    try {
      const payload = { ...form, scheduled_datetime: isoDatetime }
      if (imageFile) payload.image = imageFile
      await onSubmit(payload)
      setForm(INITIAL_STATE)
      setErrors({})
      setActiveTemplate(null)
      handleRemoveImage()
    } catch (err) {
      setErrors({ submit: err.response?.data?.error || 'Failed to schedule. Please try again.' })
    }
  }

  return (
    <div className="card">
      <h2 className="card-title">
        <span className="icon">🎂</span> Schedule a Wish
      </h2>

      <form onSubmit={handleSubmit} noValidate>
        {/* Name */}
        <div className="form-group">
          <label htmlFor="name" className="form-label">👤 Recipient Name</label>
          <input
            id="name"
            name="name"
            type="text"
            className={`form-input${errors.name ? ' error' : ''}`}
            placeholder="e.g. Priya Sharma"
            value={form.name}
            onChange={handleChange}
            autoComplete="off"
          />
          {errors.name && <p className="form-error">⚠ {errors.name}</p>}
        </div>

        {/* Phone */}
        <div className="form-group">
          <label htmlFor="phone" className="form-label">📱 Phone Number (with country code)</label>
          <input
            id="phone"
            name="phone"
            type="tel"
            className={`form-input${errors.phone ? ' error' : ''}`}
            placeholder="e.g. +919876543210"
            value={form.phone}
            onChange={handleChange}
            autoComplete="tel"
          />
          {errors.phone && <p className="form-error">⚠ {errors.phone}</p>}
        </div>

        {/* Date & Time */}
        <div className="form-group">
          <label htmlFor="scheduled_datetime" className="form-label">📅 Date & Time</label>
          <input
            id="scheduled_datetime"
            name="scheduled_datetime"
            type="datetime-local"
            className={`form-input${errors.scheduled_datetime ? ' error' : ''}`}
            min={getMinDateTime()}
            value={form.scheduled_datetime}
            onChange={handleChange}
          />
          {errors.scheduled_datetime && <p className="form-error">⚠ {errors.scheduled_datetime}</p>}
        </div>

        {/* Templates */}
        <TemplateSelector
          name={form.name}
          onSelect={handleTemplateSelect}
          activeId={activeTemplate}
          onActiveChange={setActiveTemplate}
        />

        {/* Message */}
        <div className="form-group">
          <label htmlFor="message" className="form-label">💬 Birthday Message</label>
          <textarea
            id="message"
            name="message"
            className={`form-textarea${errors.message ? ' error' : ''}`}
            placeholder="Write a heartfelt birthday message…"
            value={form.message}
            onChange={handleChange}
            rows={4}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            {errors.message
              ? <p className="form-error">⚠ {errors.message}</p>
              : <span />
            }
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              {form.message.length} chars
            </span>
          </div>
        </div>

        {/* Image Attachment */}
        <div className="form-group">
          <label className="form-label">🖼️ Attach Image <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span></label>

          {imagePreview ? (
            <div className="image-preview-wrapper">
              <img src={imagePreview} alt="Preview" className="image-preview" />
              <div className="image-preview-overlay">
                <button
                  type="button"
                  className="image-preview-remove"
                  onClick={handleRemoveImage}
                  title="Remove image"
                >✕ Remove</button>
                <span className="image-preview-name">{imageFile?.name}</span>
              </div>
            </div>
          ) : (
            <label htmlFor="image-upload" className="image-drop-zone">
              <span className="image-drop-icon">📎</span>
              <span className="image-drop-text">Click to attach an image</span>
              <span className="image-drop-sub">JPG, PNG, GIF · max {MAX_SIZE_MB}MB</span>
              <input
                id="image-upload"
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/gif"
                onChange={handleImageChange}
                style={{ display: 'none' }}
              />
            </label>
          )}
          {errors.image && <p className="form-error">⚠ {errors.image}</p>}
        </div>

        {errors.submit && (
          <div className="notification error" style={{ marginBottom: '1rem' }}>
            <span className="notification-icon">❌</span>
            <span className="notification-text">{errors.submit}</span>
          </div>
        )}

        <button
          id="submit-schedule-btn"
          type="submit"
          className="btn btn-primary"
          disabled={loading}
        >
          {loading ? '⏳ Scheduling…' : '🚀 Schedule Birthday Wish'}
        </button>
      </form>
    </div>
  )
}
