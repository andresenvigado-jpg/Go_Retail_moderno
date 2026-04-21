import { useEffect, useState } from 'react'
import { getAnomalies, getEOQ, getMonteCarlo, runAnomalies, runEOQ, runMonteCarlo } from '../api/endpoints'
import Spinner from '../components/Spinner'
import RunModelBtn from '../components/RunModelBtn'
import KPICard from '../components/KPICard'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, PieChart, Pie, Legend,
} from 'recharts'

const riskBadge = (nivel) => {
  if (!nivel) return <span className="badge badge-gray">—</span>
  const n = nivel.toLowerCase()
  if (n.includes('crítico') || n.includes('alto') || n.includes('≥70')) return <span className="badge badge-red">{nivel}</span>
  if (n.includes('medio') || n.includes('40')) return <span className="badge badge-yellow">{nivel}</span>
  if (n.includes('bajo') || n.includes('15')) return <span className="badge badge-blue">{nivel}</span>
  return <span className="badge badge-green">{nivel}</span>
}

const eoqBadge = (estado) => {
  if (!estado) return null
  if (estado.includes('Pedir ahora')) return <span className="badge badge-red">🔴 Pedir ahora</span>
  if (estado.includes('Pronto'))     return <span className="badge badge-yellow">🟡 Pedir pronto</span>
  return <span className="badge badge-green">🟢 OK</span>
}

export default function InventoryPage() {
  const [anomalies, setAnomalies] = useState(null)
  const [eoq, setEoq] = useState(null)
  const [mc, setMc] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    Promise.allSettled([
      getAnomalies({ limit: 200 }),
      getEOQ(),
      getMonteCarlo(),
    ]).then(([aR, eR, mR]) => {
      setAnomalies(aR.status === 'fulfilled' ? aR.value : null)
      setEoq(eR.status === 'fulfilled' ? eR.value : null)
      setMc(mR.status === 'fulfilled' ? mR.value : null)
      setLoading(false)
    })
  }

  useEffect(load, [])

  if (loading) return <Spinner text="Cargando inventario..." />

  // Anomaly type distribution
  const anomalyGroups = (() => {
    const counts = {}
    ;(anomalies?.data || []).filter(a => a.es_anomalia).forEach(a => {
      const k = a.tipo_anomalia.replace(/[🔴🟠🟡🔵⚪]/g, '').trim()
      counts[k] = (counts[k] || 0) + 1
    })
    return Object.entries(counts).map(([name, value]) => ({ name, value }))
  })()

  // Monte Carlo risk distribution
  const riskGroups = (() => {
    const counts = {}
    ;(mc?.data || []).forEach(r => {
      const k = r.nivel_riesgo?.replace(/[🔴🟡🟠🟢]/g, '').trim() || 'Desconocido'
      counts[k] = (counts[k] || 0) + 1
    })
    return Object.entries(counts).map(([name, value]) => ({ name, value }))
  })()

  const PIE_COLORS = ['var(--red)', 'var(--yellow)', 'var(--blue)', 'var(--green)']

  return (
    <>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
        <RunModelBtn label="Anomalías"   onRun={runAnomalies}   onSuccess={load} />
        <RunModelBtn label="EOQ"         onRun={runEOQ}         onSuccess={load} />
        <RunModelBtn label="Monte Carlo" onRun={runMonteCarlo}  onSuccess={load} />
      </div>

      <div className="kpi-grid">
        <KPICard icon="🔍" value={anomalies?.total ?? 0}    label="Registros analizados" color="blue" />
        <KPICard icon="🚨" value={anomalies?.criticas ?? 0} label="Quiebres detectados"  color="red" />
        <KPICard icon="📊" value={mc?.total ?? 0}           label="Simulaciones MC"       color="green" />
        <KPICard icon="⚠️" value={mc?.alto_riesgo ?? 0}     label="Alto riesgo quiebre"   color="yellow" />
      </div>

      <div className="grid-2">
        {/* Anomaly pie */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">🔍 Tipos de Anomalías</div>
              <div className="card-subtitle">Isolation Forest — distribución de alertas</div>
            </div>
          </div>
          {anomalyGroups.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={anomalyGroups} cx="50%" cy="50%" outerRadius={90}
                  dataKey="value" nameKey="name" label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                  labelLine={false}>
                  {anomalyGroups.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : <div className="empty-state"><div className="icon">📭</div><p>Sin anomalías detectadas.</p></div>}
        </div>

        {/* MC risk */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">🎲 Monte Carlo — Nivel de Riesgo</div>
              <div className="card-subtitle">Probabilidad de quiebre de stock</div>
            </div>
          </div>
          {riskGroups.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={riskGroups} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
                <YAxis tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {riskGroups.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <div className="empty-state"><div className="icon">📭</div><p>Sin datos Monte Carlo.</p></div>}
        </div>
      </div>

      {/* EOQ Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">📦 EOQ — Cantidad Óptima de Pedido</div>
            <div className="card-subtitle">{eoq?.total ?? 0} combinaciones SKU-Tienda</div>
          </div>
        </div>
        <div className="table-wrap" style={{ maxHeight: 320, overflowY: 'auto' }}>
          <table>
            <thead>
              <tr><th>SKU</th><th>Tienda</th><th>EOQ</th><th>Punto Reorden</th><th>Stock Seg.</th><th>Días entre pedidos</th><th>Estado</th></tr>
            </thead>
            <tbody>
              {(eoq?.data || []).slice(0, 50).map((r, i) => (
                <tr key={i}>
                  <td><span className="badge badge-green">{r.sku_id}</span></td>
                  <td style={{ color: 'var(--text-secondary)' }}>{r.tienda_id}</td>
                  <td style={{ fontWeight: 600 }}>{Number(r.eoq).toFixed(0)}</td>
                  <td>{Number(r.punto_reorden).toFixed(0)}</td>
                  <td>{Number(r.stock_seguridad).toFixed(0)}</td>
                  <td>{r.dias_entre_pedidos != null ? Number(r.dias_entre_pedidos).toFixed(0) : '—'}</td>
                  <td>{eoqBadge(r.estado_reposicion)}</td>
                </tr>
              ))}
              {!eoq?.data?.length && <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: 24 }}>Sin datos EOQ</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      {/* Anomalies Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">🚨 Detalle de Anomalías</div>
            <div className="card-subtitle">Solo registros con anomalía detectada</div>
          </div>
        </div>
        <div className="table-wrap" style={{ maxHeight: 300, overflowY: 'auto' }}>
          <table>
            <thead>
              <tr><th>SKU</th><th>Tienda</th><th>Tipo</th><th>Score</th><th>Stock</th><th>Cobertura</th></tr>
            </thead>
            <tbody>
              {(anomalies?.data || []).filter(a => a.es_anomalia).slice(0, 50).map((a, i) => (
                <tr key={i}>
                  <td><span className="badge badge-red">{a.sku_id}</span></td>
                  <td style={{ color: 'var(--text-secondary)' }}>{a.tienda_id}</td>
                  <td style={{ fontSize: '0.78rem' }}>{a.tipo_anomalia}</td>
                  <td>{Number(a.score_anomalia).toFixed(3)}</td>
                  <td>{a.stock_actual != null ? Number(a.stock_actual).toFixed(0) : '—'}</td>
                  <td>{a.cobertura_dias != null ? `${Number(a.cobertura_dias).toFixed(1)} días` : '—'}</td>
                </tr>
              ))}
              {!anomalies?.data?.filter(a => a.es_anomalia).length && (
                <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: 24 }}>Sin anomalías</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
