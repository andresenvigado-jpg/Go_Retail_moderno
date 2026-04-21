import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handle = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.username, form.password)
      navigate('/')
    } catch (err) {
      const msg = err.response?.data?.detail || err.response?.data?.message || err.message
      setError(msg || 'Credenciales incorrectas')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <h1>Go Retail</h1>
          <p>Supply Chain Intelligence API</p>
        </div>

        {error && <div className="error-msg">{error}</div>}

        <form onSubmit={handle}>
          <div className="form-group">
            <label>Usuario</label>
            <input
              type="text"
              placeholder="username"
              value={form.username}
              onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
              autoFocus
              required
            />
          </div>
          <div className="form-group">
            <label>Contraseña</label>
            <input
              type="password"
              placeholder="••••••••"
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              required
            />
          </div>
          <button className="btn-login" type="submit" disabled={loading}>
            {loading ? 'Autenticando...' : 'Iniciar sesión'}
          </button>
        </form>
      </div>
    </div>
  )
}
