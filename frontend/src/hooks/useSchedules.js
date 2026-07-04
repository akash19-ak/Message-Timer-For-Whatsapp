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
    const { data } = await axios.post(`${BASE}/schedule`, payload)
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
    const { data } = await axios.put(`${BASE}/schedule/${id}`, payload)
    setSchedules(prev => prev.map(s => s.id === id ? data : s))
    return data
  }, [])

  useEffect(() => {
    fetchSchedules()
    // Poll every 60 seconds to refresh sent status
    const interval = setInterval(fetchSchedules, 60000)
    return () => clearInterval(interval)
  }, [fetchSchedules])

  return { schedules, loading, error, fetchSchedules, createSchedule, deleteSchedule, updateSchedule }
}
