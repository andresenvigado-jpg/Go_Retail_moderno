import { useEffect, useState } from 'react'
import { getForecasts, getPredictions, runLightGBM } from '../api/endpoints'
import Spinner from '../components/Spinner'
import RunModelBtn from '../components/RunModelBtn'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ScatterChart, Scatter, ReferenceLine,
} from 'recharts'

const fmt = (n) => (n == null ? '—' : Number(n).toFixed(1))

export default function DemandPage() {
  const [forecasts, setForecasts] = useState(null)
  const [predictions, setPredictions] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    Promise.allSettled([
      getForecasts({ limit: 300 }),
      getPredictions({ limit: 300 }),
    ]).then(([fcR, pdR]) => {
      setForecasts(fcR.status === 'fulfilled' ? fcR.value : null)
      setPredictions(pdR.status === 'fulfilled' ? pdR.value : null)
      setLoading(false)
    })
  }

  useEffect(load, [])

  if (loading) return <Spinner text="Cargando datos de demanda..." />

  // Group forecasts by SKU for chart
  const skus = [...new Set((forecasts?.data || []).map(f => f.sku_id))].slice(0, 5)
  const colors = ['var(--green)', 'var(--blue)', 'var(--yellow)', '#e879f9', '#fb923c']

  const chartData = (() => {
    const byDate = {}
    ;(forecasts?.data || []).filter(f => skus.includes(f.sku_id)).forEach(f => {
      const d = String(f.fecha)
      if (!byDate[d]) byDate[d] = { fecha: d }
      byDate[d][`SKU ${f.sku_id}`] = Number(f.demanda_estimada).toFixed(1)
    })
    return Object.values(byDate).sort((a, b) => a.fecha.localeCompare(b.fecha)).slice(0, 30)
  })()

  // Scatter: real vs predicted
  const scatterData = (predictions?.data || [])
    .filter(p => p.cantidad_real != null)
    .slice(0, 100)
    .map(p => ({ real: +p.cantidad_real, pred: +p.cantidad_predicha }))

  return (
    <>
      <RunModelBtn label="Ejecutar LightGBM" onRun={runLightGBM} onSuccess={load} />

      {/* Forecasts Chart */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">📈 Pronóstico Prophet — Top 5 SKUs</div>
            <div className="card-subtitle">
              {forecasts?.total ? `${forecasts.total} registros · próximos 30 días` : 'Sin datos'}
            </div>
          </div>
        </div>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData} margin={{ top: 0, right: 16, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="fecha" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} tickFormatter={v => v.slice(5)} />
              <YAxis tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {skus.map((sku, i) => (
                <Line key={sku} type="monotone" dataKey={`SKU ${sku}`}
                  stroke={colors[i]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty-state">
            <div className="icon">📭</div>
            <p>Sin pronósticos. Ejecuta el modelo Prophet desde la API.</p>
          </div>
        )}
      </div>

      <div className="grid-2">
        {/* LightGBM Scatter */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">🤖 LightGBM — Real vs Predicho</div>
              <div className="card-subtitle">
                {predictions?.mae != null ? `MAE: ${fmt(predictions.mae)} unidades` : `${predictions?.total ?? 0} predicciones`}
              </div>
            </div>
          </div>
          {scatterData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <ScatterChart margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="real" name="Real" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} label={{ value: 'Real', position: 'insideBottom', offset: -2, fontSize: 11 }} />
                <YAxis dataKey="pred" name="Predicho" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                  formatter={(v) => [fmt(v)]}
                />
                <ReferenceLine stroke="var(--green)" strokeDasharray="4 4"
                  segment={[{ x: 0, y: 0 }, { x: Math.max(...scatterData.map(d => d.real)), y: Math.max(...scatterData.map(d => d.real)) }]} />
                <Scatter data={scatterData} fill="var(--blue)" opacity={0.6} />
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state"><div className="icon">📭</div><p>Sin predicciones LightGBM.</p></div>
          )}
        </div>

        {/* Forecasts Table */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">📋 Detalle de pronósticos</div>
          </div>
          <div className="table-wrap" style={{ maxHeight: 280, overflowY: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>SKU</th><th>Fecha</th><th>Estimado</th><th>Mín</th><th>Máx</th>
                </tr>
              </thead>
              <tbody>
                {(forecasts?.data || []).slice(0, 50).map((f, i) => (
                  <tr key={i}>
                    <td><span className="badge badge-green">{f.sku_id}</span></td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>{String(f.fecha)}</td>
                    <td style={{ fontWeight: 600 }}>{fmt(f.demanda_estimada)}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{fmt(f.demanda_minima)}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{fmt(f.demanda_maxima)}</td>
                  </tr>
                ))}
                {!forecasts?.data?.length && (
                  <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: 24 }}>Sin datos</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  )
}
