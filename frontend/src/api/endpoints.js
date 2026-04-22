import client from './client'
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

// ── Auth ─────────────────────────────────────────────────────────
export const login = async (username, password) => {
  const params = new URLSearchParams()
  params.append('username', username)
  params.append('password', password)
  const { data } = await axios.post(`${BASE_URL}/auth/login`, params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}