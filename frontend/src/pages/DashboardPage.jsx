import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAnomalies, getMonteCarlo, getForecasts, getProducts, getStores } from '../api/endpoints'
import KPICard from '../components/KPICard'
import Spinner from '../components/Spinner'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

export default function DashboardPage() {
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.allSettled([
      getAnomalies({ limit: 500 }),
      getMonteCarlo({ }),
      getForecasts({ limit: 300 }),
      getProducts({ limit: 200 }),
      getStores(),
    ]).then(([anomR, mcR, fcR, prodR, storeR]) => {
      setData({
        anomalies:   anomR.status === 'fulfilled' ? anomR.value : null,
        monteCarlo:  mcR.status   === 'fulfilled' ? mcR.value   : null,
        forecasts:   fcR.status   === 'fulfilled' ? fcR.value   : null,
        products:    prodR.status === 'fulfilled' ? prodR.value : [],
        stores:      storeR.status=== 'fulfilled' ? storeR.value: [],
      })
      setLoading(false)
    })
  }, [])

  if (loading) return <Spinner text="Cargando dashboard..." />

  // Top SKUs by forecast demand
  const forecastChart = (() => {
    if (!data.forecasts?.data?.length) return []
    const bysku = {}
    data.forecasts.data.forEach(f => {
      bysku[f.sku_id] = (bysku[f.sku_id] || 0) + f.demanda_estimada
    })
    return Object.entries(bysku)
      .map(([sku, val]) => ({ sku: `SKU ${sku}`, demanda: Math.round(val) }))
      .sort((a, b) => b.demanda - a.demanda)
      .slice(0, 8)
  })()

  const criticas = data.anomalies?.criticas ?? 0
  const altoRiesgo = data.monteCarlo?.alto_riesgo ?? 0
  const totalSkus = data.products?.length ?? 0
  const totalStores = data.stores?.length ?? 0

  const quickLinks = [
    { label: '📈 Ver Pronósticos',   to: '/demand',    color: 'var(--green)' },
    { label: '📦 Ver Anomalías',     to: '/inventory', color: 'var(--red)' },
    { label: '💰 Ver Rentabilidad',  to: '/analytics', color: 'var(--yellow)' },
    { label: '🛍️ Ver Segmentación', to: '/products',  color: 'var(--blue)' },
  ]

  return (
    <>
      <div className="kpi-grid">
        <KPICard icon="🛍️" value={totalSkus}   label="Total SKUs"           color="green" />
        <KPICard icon="🏪" value={totalStores} label="Tiendas activas"       color="blue" />
        <KPICard icon="🚨" value={criticas}    label="Quiebres de stock"     color="red" />
        <KPICard icon="⚠️" value={altoRiesgo}  label="SKUs en alto riesgo"   color="yellow" />
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">📈 Pronóstico de Demanda</div>
              <div className="card-subtitle">Demanda estimada total por SKU (próximos 30 días)</div>
            </div>
          </div>
          {forecastChart.length > 0 ? (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={forecastChart} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="sku" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
                  <YAxis tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
                  <Tooltip
                    contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }}
                    labelStyle={{ color: 'var(--text-primary)' }}
                  />
                  <Bar dataKey="demanda" radius={[4, 4, 0, 0]}>
                    {forecastChart.map((_, i) => (
                      <Cell key={i} fill={i === 0 ? 'var(--green)' : 'var(--green-dark)'} opacity={1 - i * 0.08} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-state">
              <div className="icon">📭</div>
              <p>Sin datos de pronóstico. Ejecuta el modelo desde la sección Demanda.</p>
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">⚡ Accesos rápidos</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {quickLinks.map(link => (
              <button
                key={link.to}
                className="btn btn-secondary"
                style={{ justifyContent: 'flex-start', padding: '14px 16px', borderColor: 'var(--border)' }}
                onClick={() => navigate(link.to)}
              >
                {link.label}
              </button>
            ))}
          </div>

          <div style={{ marginTop: 24 }}>
            <div className="card-title" style={{ marginBottom: 12 }}>📊 Estado del sistema</div>
            {[
              { label: 'Pronósticos', ok: !!data.forecasts?.total },
              { label: 'Anomalías',   ok: !!data.anomalies?.total },
              { label: 'Monte Carlo', ok: !!data.monteCarlo?.total },
            ].map(s => (
              <div key={s.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.82rem' }}>{s.label}</span>
                <span className={`badge ${s.ok ? 'badge-green' : 'badge-gray'}`}>
                  {s.ok ? 'Con datos' : 'Sin datos'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}
