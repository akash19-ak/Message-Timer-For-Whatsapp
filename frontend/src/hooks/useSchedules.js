import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

const BASE = '/api'

export function useSchedules() {
  const [schedules, setSchedules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchSchedules = useCallback(async () => {
    try {
      setLoading(true)
      const { data } = await axios.get(`${BASE}/schedules`)
      setSchedules(data)
      setError(null)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load schedules.')
    } finally {
      setLoading(false)
    }
  }, [])

  const createSchedule = useCallback(async (payload) => {
    // If payload contains an image file, use FormData; otherwise use JSON
    let body
    let headers = {}
    if (payload.image instanceof File) {
      body = new FormData()
      Object.entries(payload).forEach(([k, v]) => {
        if (v !== null && v !== undefined) body.append(k, v)
      })
      // Let browser set multipart boundary automatically
    } else {
      body = JSON.stringify(payload)
      headers['Content-Type'] = 'application/json'
    }
    const { data } = await axios.post(`${BASE}/schedule`, body, { headers })
    setSchedules(prev => [...prev, data].sort(
      (a, b) => new Date(a.scheduled_datetime) - new Date(b.scheduled_datetime)
    ))
    return data
  }, [])

  const deleteSchedule = useCallback(async (id) => {
    await axios.delete(`${BASE}/schedule/${id}`)
    setSchedules(prev => prev.filter(s => s.id !== id))
  }, [])

  const updateSchedule = useCallback(async (id, payload) => {
    let body
    let headers = {}
    if (payload.image instanceof File || payload.remove_image) {
      body = new FormData()
      Object.entries(payload).forEach(([k, v]) => {
        if (v !== null && v !== undefined) body.append(k, v instanceof File ? v : String(v))
      })
    } else {
      body = JSON.stringify(payload)
      headers['Content-Type'] = 'application/json'
    }
    const { data } = await axios.put(`${BASE}/schedule/${id}`, body, { headers })
    setSchedules(prev => prev.map(s => s.id === id ? data : s))
    return data
  }, [])

  const sendNow = useCallback(async (id, method = 'app') => {
    const { data } = await axios.post(`${BASE}/schedule/${id}/send`, { method })
    // Refresh list after 3s to reflect sent=true
    setTimeout(fetchSchedules, 3000)
    return data
  }, [fetchSchedules])

  useEffect(() => {
    fetchSchedules()
    // Poll every 60 seconds to refresh sent status
    const interval = setInterval(fetchSchedules, 60000)
    return () => clearInterval(interval)
  }, [fetchSchedules])

  return { schedules, loading, error, fetchSchedules, createSchedule, deleteSchedule, updateSchedule, sendNow }
}
