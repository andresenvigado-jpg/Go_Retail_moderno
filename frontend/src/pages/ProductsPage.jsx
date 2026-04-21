import { useEffect, useState } from 'react'
import { getSegmentation, getMarketBasket, runSegmentation, runMarketBasket } from '../api/endpoints'
import Spinner from '../components/Spinner'
import RunModelBtn from '../components/RunModelBtn'
import KPICard from '../components/KPICard'
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts'

export default function ProductsPage() {
  const [seg, setSeg] = useState(null)
  const [basket, setBasket] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    Promise.allSettled([
      getSegmentation(),
      getMarketBasket({ min_lift: 1.0 }),
    ]).then(([sR, bR]) => {
      setSeg(sR.status === 'fulfilled' ? sR.value : null)
      setBasket(bR.status === 'fulfilled' ? bR.value : null)
      setLoading(false)
    })
  }

  useEffect(load, [])

  if (loading) return <Spinner text="Cargando productos..." />

  const abcData = [
    { name: 'Segmento A', value: seg?.segmento_a ?? 0, color: 'var(--green)' },
    { name: 'Segmento B', value: seg?.segmento_b ?? 0, color: 'var(--yellow)' },
    { name: 'Segmento C', value: seg?.segmento_c ?? 0, color: 'var(--text-secondary)' },
  ].filter(d => d.value > 0)

  const topBasket = (basket?.data || [])
    .slice(0, 10)
    .map(r => ({ pair: `${r.sku_origen}→${r.sku_destino}`, lift: Number(r.lift).toFixed(2) }))

  return (
    <>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
        <RunModelBtn label="Segmentación ABC" onRun={runSegmentation} onSuccess={load} />
        <RunModelBtn label="Market Basket"    onRun={runMarketBasket} onSuccess={load} />
      </div>

      <div className="kpi-grid">
        <KPICard icon="🅰️" value={seg?.segmento_a ?? 0} label="SKUs Segmento A (70% ventas)" color="green" />
        <KPICard icon="🅱️" value={seg?.segmento_b ?? 0} label="SKUs Segmento B (20% ventas)" color="yellow" />
        <KPICard icon="🇨"  value={seg?.segmento_c ?? 0} label="SKUs Segmento C (10% ventas)" color="blue" />
        <KPICard icon="🔗" value={basket?.total ?? 0}    label="Reglas de asociación"          color="green" />
      </div>

      <div className="grid-2">
        {/* ABC Pie */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">🛍️ Segmentación ABC</div>
              <div className="card-subtitle">Clasificación por participación en ventas</div>
            </div>
          </div>
          {abcData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={abcData} cx="50%" cy="50%" outerRadius={100}
                  dataKey="value" nameKey="name"
                  label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                  labelLine={true}>
                  {abcData.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Pie>
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : <div className="empty-state"><div className="icon">📭</div><p>Sin datos de segmentación.</p></div>}
        </div>

        {/* Market Basket lift chart */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">🔗 Market Basket — Top Lift</div>
              <div className="card-subtitle">Pares de SKUs con mayor asociación</div>
            </div>
          </div>
          {topBasket.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={topBasket} layout="vertical" margin={{ top: 0, right: 16, left: 60, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
                <YAxis dataKey="pair" type="category" tick={{ fontSize: 9, fill: 'var(--text-secondary)' }} width={60} />
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="lift" name="Lift" fill="var(--green)" radius={[0,4,4,0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <div className="empty-state"><div className="icon">📭</div><p>Sin reglas de asociación.</p></div>}
        </div>
      </div>

      {/* ABC table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">📋 Detalle Segmentación ABC</div>
        </div>
        <div className="table-wrap" style={{ maxHeight: 280, overflowY: 'auto' }}>
          <table>
            <thead>
              <tr><th>SKU</th><th>Participación %</th><th>Acumulado %</th><th>Segmento</th></tr>
            </thead>
            <tbody>
              {(seg?.data || []).slice(0, 40).map((r, i) => (
                <tr key={i}>
                  <td><span className="badge badge-blue">{r.sku_id}</span></td>
                  <td>{Number(r.participacion).toFixed(2)}%</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div className="progress-bar" style={{ width: 80 }}>
                        <div className="progress-fill" style={{
                          width: `${Math.min(r.acumulado, 100)}%`,
                          background: r.segmento_abc === 'A' ? 'var(--green)' : r.segmento_abc === 'B' ? 'var(--yellow)' : 'var(--text-secondary)',
                        }} />
                      </div>
                      {Number(r.acumulado).toFixed(1)}%
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${r.segmento_abc === 'A' ? 'badge-green' : r.segmento_abc === 'B' ? 'badge-yellow' : 'badge-gray'}`}>
                      {r.segmento_abc}
                    </span>
                  </td>
                </tr>
              ))}
              {!seg?.data?.length && <tr><td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: 24 }}>Sin datos</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      {/* Market basket table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">🔗 Reglas de Asociación</div>
        </div>
        <div className="table-wrap" style={{ maxHeight: 280, overflowY: 'auto' }}>
          <table>
            <thead>
              <tr><th>SKU Origen</th><th>SKU Destino</th><th>Soporte</th><th>Confianza</th><th>Lift</th></tr>
            </thead>
            <tbody>
              {(basket?.data || []).slice(0, 30).map((r, i) => (
                <tr key={i}>
                  <td><span className="badge badge-green">{r.sku_origen}</span></td>
                  <td><span className="badge badge-blue">{r.sku_destino}</span></td>
                  <td>{Number(r.soporte).toFixed(3)}</td>
                  <td>{Number(r.confianza).toFixed(3)}</td>
                  <td>
                    <span className={`badge ${+r.lift >= 3 ? 'badge-green' : +r.lift >= 2 ? 'badge-yellow' : 'badge-gray'}`}>
                      {Number(r.lift).toFixed(2)}
                    </span>
                  </td>
                </tr>
              ))}
              {!basket?.data?.length && <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: 24 }}>Sin reglas</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
