import { createContext, useContext, useState, useEffect } from 'react'
import { login as apiLogin, getMe } from '../api/endpoints'
import client from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('user')) } catch { return null }
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token && !user) {
      getMe()
        .then(setUser)
        .catch(() => { localStorage.removeItem('access_token') })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (username, password) => {
    const data = await apiLogin(username, password)
    localStorage.setItem('access_token', data.access_token)
    const me = await getMe()
    localStorage.setItem('user', JSON.stringify(me))
    setUser(me)

    // Validar y cargar datos del día en segundo plano (sin bloquear)
    client.post('/admin/check-and-load')
      .then(r => console.log('✅ Datos verificados:', r.data?.message))
      .catch(e => console.warn('⚠️ Check-and-load:', e.message))

    return me
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
