import { useState } from 'react'

export default function RunModelBtn({ label, onRun, onSuccess }) {
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)

  const handle = async () => {
    setRunning(true)
    setResult(null)
    try {
      const r = await onRun()
      setResult({ ok: true, msg: r.message || `${r.records_saved} registros guardados` })
      if (onSuccess) onSuccess()
    } catch (e) {
      const msg = e.response?.data?.detail || e.response?.data?.message || e.message || 'Error ejecutando modelo'
      setResult({ ok: false, msg })
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="run-bar">
      <p>Ejecuta el modelo y actualiza los resultados en la base de datos.</p>
      {result && (
        <span style={{ color: result.ok ? 'var(--green)' : 'var(--red)', fontSize: '0.8rem' }}>
          {result.ok ? '✓' : '✗'} {result.msg}
        </span>
      )}
      <button className="btn btn-primary" onClick={handle} disabled={running}>
        {running ? '⏳ Ejecutando...' : `▶ ${label}`}
      </button>
    </div>
  )
}
