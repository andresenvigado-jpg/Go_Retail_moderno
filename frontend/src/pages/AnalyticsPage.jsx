import { useEffect, useState } from 'react'
import { getRentability, getRotation, getEfficiency, runRentability, runRotation, runEfficiency } from '../api/endpoints'
import Spinner from '../components/Spinner'
import RunModelBtn from '../components/RunModelBtn'
import KPICard from '../components/KPICard'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, PieChart, Pie, Legend, RadarChart,
  PolarGrid, PolarAngleAxis, Radar,
} from 'recharts'

const classBadge = (c) => {
  if (!c) return null
  if (c.includes('Alta') || c.includes('alta') || c.includes('🟢') || Number(c) >= 70)
    return <span className="badge badge-green">{c}</span>
  if (c.includes('Media') || c.includes('media') || c.includes('🟡'))
    return <span className="badge badge-yellow">{c}</span>
  return <span className="badge badge-red">{c}</span>
}

export default function AnalyticsPage() {
  const [rent, setRent] = useState(null)
  const [rot, setRot] = useState(null)
  const [eff, setEff] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    Promise.allSettled([
      getRentability({ limit: 100 }),
      getRotation({ limit: 100 }),
      getEfficiency(),
    ]).then(([rR, rotR, eR]) => {
      setRent(rR.status === 'fulfilled' ? rR.value : null)
      setRot(rotR.status === 'fulfilled' ? rotR.value : null)
      setEff(eR.status === 'fulfilled' ? eR.value : null)
      setLoading(false)
    })
  }

  useEffect(load, [])

  if (loading) return <Spinner text="Cargando analítica..." />

  const topRent = (rent?.data || []).slice(0, 12).map(r => ({
    sku: `SKU ${r.sku_id}`,
    margen: Number(r.margen_porcentual).toFixed(1),
    indice: Number(r.indice_rentabilidad).toFixed(1),
  }))

  const rotClasses = (() => {
    const c = {}
    ;(rot?.data || []).forEach(r => {
      const k = r.clasificacion?.replace(/[🚀🔄🐢❄️]/g, '').trim() || 'N/A'
      c[k] = (c[k] || 0) + 1
    })
    return Object.entries(c).map(([name, value]) => ({ name, value }))
  })()

  const topEff = (eff?.data || []).slice(0, 8).map(e => ({
    tienda: `T-${e.tienda_id}`,
    eficiencia: Number(e.indice_eficiencia).toFixed(1),
    cobertura: Number(e.cobertura_reposicion).toFixed(1),
  }))

  const PIE_COLORS = ['var(--green)', 'var(--yellow)', 'var(--blue)', 'var(--text-secondary)']

  return (
    <>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
        <RunModelBtn label="Rentabilidad" onRun={runRentability} onSuccess={load} />
        <RunModelBtn label="Rotación"     onRun={runRotation}    onSuccess={load} />
        <RunModelBtn label="Eficiencia"   onRun={runEfficiency}  onSuccess={load} />
      </div>

      <div className="kpi-grid">
        <KPICard icon="💰" value={rent?.total ?? 0}    label="SKUs analizados (rent.)" color="green" />
        <KPICard icon="📊" value={rent?.promedio_margen != null ? `${Number(rent.promedio_margen).toFixed(1)}%` : '—'} label="Margen promedio" color="blue" />
        <KPICard icon="🏪" value={eff?.total ?? 0}    label="Tiendas evaluadas"        color="yellow" />
        <KPICard icon="⚡" value={eff?.promedio_eficiencia != null ? Number(eff.promedio_eficiencia).toFixed(1) : '—'} label="Eficiencia promedio" color="green" />
      </div>

      {/* Rentability bar */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">💰 Índice de Rentabilidad — Top SKUs</div>
            <div className="card-subtitle">Margen % por SKU · ordenado por índice</div>
          </div>
        </div>
        {topRent.length > 0 ? (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={topRent} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="sku" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
              <YAxis tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
              <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="margen" name="Margen %" radius={[4,4,0,0]}>
                {topRent.map((r, i) => (
                  <Cell key={i} fill={+r.indice >= 70 ? 'var(--green)' : +r.indice >= 40 ? 'var(--yellow)' : 'var(--red)'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : <div className="empty-state"><div className="icon">📭</div><p>Sin datos de rentabilidad.</p></div>}
      </div>

      <div className="grid-2">
        {/* Rotation pie */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">🔄 Clasificación de Rotación</div>
              <div className="card-subtitle">Velocidad de inventario por SKU</div>
            </div>
          </div>
          {rotClasses.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={rotClasses} cx="50%" cy="50%" outerRadius={85}
                  dataKey="value" nameKey="name"
                  label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                  labelLine={false}>
                  {rotClasses.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : <div className="empty-state"><div className="icon">📭</div><p>Sin datos de rotación.</p></div>}
        </div>

        {/* Efficiency bar */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">🏪 Eficiencia de Reposición</div>
              <div className="card-subtitle">Índice de eficiencia por tienda</div>
            </div>
          </div>
          {topEff.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={topEff} layout="vertical" margin={{ top: 0, right: 16, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
                <YAxis dataKey="tienda" type="category" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} width={40} />
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="eficiencia" name="Índice" radius={[0,4,4,0]}>
                  {topEff.map((r, i) => (
                    <Cell key={i} fill={+r.eficiencia >= 70 ? 'var(--green)' : +r.eficiencia >= 45 ? 'var(--yellow)' : 'var(--red)'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <div className="empty-state"><div className="icon">📭</div><p>Sin datos de eficiencia.</p></div>}
        </div>
      </div>

      {/* Rentability detail table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">📋 Detalle de Rentabilidad</div>
        </div>
        <div className="table-wrap" style={{ maxHeight: 300, overflowY: 'auto' }}>
          <table>
            <thead>
              <tr><th>SKU</th><th>Margen %</th><th>Rentabilidad Total</th><th>Índice</th><th>Clasificación</th></tr>
            </thead>
            <tbody>
              {(rent?.data || []).slice(0, 30).map((r, i) => (
                <tr key={i}>
                  <td><span className="badge badge-blue">{r.sku_id}</span></td>
                  <td>{Number(r.margen_porcentual).toFixed(1)}%</td>
                  <td>${Number(r.rentabilidad_total).toLocaleString('es-CO', { maximumFractionDigits: 0 })}</td>
                  <td style={{ fontWeight: 600 }}>{Number(r.indice_rentabilidad).toFixed(1)}</td>
                  <td>{classBadge(r.clasificacion)}</td>
                </tr>
              ))}
              {!rent?.data?.length && <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: 24 }}>Sin datos</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
