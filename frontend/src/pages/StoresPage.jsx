import { useEffect, useState } from 'react'
import { getStores, getStoreSegmentation, getEfficiency } from '../api/endpoints'
import Spinner from '../components/Spinner'
import KPICard from '../components/KPICard'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts'

const formatBadge = (f) => {
  if (!f) return null
  const map = { grande: 'badge-green', mediano: 'badge-blue', pequeño: 'badge-yellow', express: 'badge-gray' }
  return <span className={`badge ${map[f?.toLowerCase()] || 'badge-gray'}`}>{f}</span>
}

export default function StoresPage() {
  const [stores, setStores] = useState([])
  const [seg, setSeg] = useState([])
  const [eff, setEff] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.allSettled([getStores(), getStoreSegmentation(), getEfficiency()]).then(([sR, sgR, eR]) => {
      setStores(sR.status === 'fulfilled' ? sR.value : [])
      setSeg(sgR.status === 'fulfilled' ? sgR.value : [])
      setEff(eR.status === 'fulfilled' ? eR.value : null)
      setLoading(false)
    })
  }, [])

  if (loading) return <Spinner text="Cargando tiendas..." />

  const effChart = (eff?.data || []).slice(0, 10).map(e => ({
    tienda: `T-${e.tienda_id}`,
    eficiencia: Number(e.indice_eficiencia).toFixed(1),
  }))

  const byFormato = stores.reduce((acc, s) => {
    const k = s.formato || 'N/A'
    acc[k] = (acc[k] || 0) + 1
    return acc
  }, {})

  return (
    <>
      <div className="kpi-grid">
        <KPICard icon="🏪" value={stores.length}                                    label="Total tiendas"           color="green" />
        <KPICard icon="🏙️" value={[...new Set(stores.map(s => s.ciudad))].length}   label="Ciudades"                color="blue" />
        <KPICard icon="📦" value={seg.length}                                       label="Clusters K-Means"        color="yellow" />
        <KPICard icon="⚡" value={eff?.promedio_eficiencia != null ? `${Number(eff.promedio_eficiencia).toFixed(1)}` : '—'} label="Eficiencia promedio" color="green" />
      </div>

      <div className="grid-2">
        {/* Efficiency ranking */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">⚡ Ranking de Eficiencia</div>
              <div className="card-subtitle">Índice de reposición por tienda</div>
            </div>
          </div>
          {effChart.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={effChart} layout="vertical" margin={{ top: 0, right: 16, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
                <YAxis dataKey="tienda" type="category" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} width={44} />
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="eficiencia" name="Índice" radius={[0,4,4,0]}>
                  {effChart.map((r, i) => (
                    <Cell key={i} fill={+r.eficiencia >= 70 ? 'var(--green)' : +r.eficiencia >= 45 ? 'var(--yellow)' : 'var(--red)'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <div className="empty-state"><div className="icon">📭</div><p>Sin datos de eficiencia.</p></div>}
        </div>

        {/* Format distribution */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">🏗️ Distribución por Formato</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
            {Object.entries(byFormato).map(([fmt, count]) => (
              <div key={fmt} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                {formatBadge(fmt)}
                <div className="progress-bar" style={{ flex: 1 }}>
                  <div className="progress-fill" style={{
                    width: `${(count / stores.length) * 100}%`,
                    background: 'var(--green)',
                  }} />
                </div>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', minWidth: 24 }}>{count}</span>
              </div>
            ))}
            {!stores.length && <div className="empty-state"><div className="icon">📭</div><p>Sin tiendas.</p></div>}
          </div>
        </div>
      </div>

      {/* Stores table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">📋 Catálogo de Tiendas</div>
        </div>
        <div className="table-wrap" style={{ maxHeight: 360, overflowY: 'auto' }}>
          <table>
            <thead>
              <tr><th>ID</th><th>Nombre</th><th>Ciudad</th><th>Región</th><th>Formato</th><th>Clima</th><th>Zona</th></tr>
            </thead>
            <tbody>
              {stores.map((s, i) => (
                <tr key={i}>
                  <td><span className="badge badge-gray">{s.tienda_id}</span></td>
                  <td style={{ fontWeight: 500 }}>{s.nombre}</td>
                  <td>{s.ciudad}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>{s.region}</td>
                  <td>{formatBadge(s.formato)}</td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>{s.clima || '—'}</td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>{s.zona || '—'}</td>
                </tr>
              ))}
              {!stores.length && <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: 24 }}>Sin tiendas</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      {/* Segmentation table */}
      {seg.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">🗂️ Segmentación K-Means de Tiendas</div>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Tienda</th><th>Ventas Totales</th><th>Venta Prom.</th><th>SKUs</th><th>Segmento</th></tr>
              </thead>
              <tbody>
                {seg.slice(0, 20).map((s, i) => (
                  <tr key={i}>
                    <td><span className="badge badge-blue">{s.tienda_id}</span></td>
                    <td>${Number(s.ventas_totales).toLocaleString('es-CO', { maximumFractionDigits: 0 })}</td>
                    <td>{Number(s.venta_promedio).toFixed(1)}</td>
                    <td>{s.num_skus}</td>
                    <td><span className="badge badge-green">{s.segmento_tienda}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}
