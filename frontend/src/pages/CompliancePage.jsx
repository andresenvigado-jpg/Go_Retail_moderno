import { useState, useEffect, useCallback } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, Cell, ReferenceLine,
} from 'recharts'
import { getComplianceReport } from '../api/endpoints'
import Spinner from '../components/Spinner'

// ── Paleta de colores por tier ────────────────────────────────────
const TIER_COLOR = {
  'Excelente 🏆': '#22c55e',
  'Bueno ✅':     '#3b82f6',
  'Regular ⚠️':  '#f59e0b',
  'Crítico 🚨':   '#ef4444',
}

const TEND_COLOR = {
  'Mejorando ↑': '#22c55e',
  'Estable →':   '#94a3b8',
  'Bajando ↓':   '#ef4444',
  'Sin datos':   '#94a3b8',
}

// ── Helpers ───────────────────────────────────────────────────────
const fmt = (n, dec = 0) =>
  Number(n).toLocaleString('es-CO', { minimumFractionDigits: dec, maximumFractionDigits: dec })

const fmtCOP = (n) =>
  `$${Number(n / 1_000_000).toLocaleString('es-CO', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}M`

const pctColor = (p) =>
  p >= 100 ? '#22c55e' : p >= 80 ? '#f59e0b' : '#ef4444'

// ── Componente: tarjeta KPI ───────────────────────────────────────
function KpiCard({ label, value, sub, color = '#3b82f6', icon }) {
  return (
    <div style={{
      background: '#1e293b', borderRadius: 12, padding: '18px 20px',
      borderLeft: `4px solid ${color}`, flex: 1, minWidth: 160,
    }}>
      <div style={{ fontSize: 22, marginBottom: 4 }}>{icon}</div>
      <div style={{ fontSize: 26, fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>{label}</div>
      {sub && <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>{sub}</div>}
    </div>
  )
}

// ── Componente: badge tier ────────────────────────────────────────
function TierBadge({ tier }) {
  const color = TIER_COLOR[tier] || '#94a3b8'
  return (
    <span style={{
      background: color + '22', color, border: `1px solid ${color}`,
      borderRadius: 6, padding: '2px 8px', fontSize: 11, fontWeight: 600,
      whiteSpace: 'nowrap',
    }}>
      {tier}
    </span>
  )
}

// ── Componente: badge tendencia ───────────────────────────────────
function TendBadge({ tendencia }) {
  const color = TEND_COLOR[tendencia] || '#94a3b8'
  return (
    <span style={{ color, fontWeight: 600, fontSize: 13 }}>{tendencia}</span>
  )
}

// ── Tooltip personalizado para gráfica ────────────────────────────
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload || {}
  return (
    <div style={{
      background: '#1e293b', border: '1px solid #334155',
      borderRadius: 8, padding: '10px 14px', fontSize: 12,
    }}>
      <div style={{ fontWeight: 700, marginBottom: 6, color: '#e2e8f0' }}>{label}</div>
      <div style={{ color: '#94a3b8' }}>Cumplimiento: <span style={{ color: pctColor(d.pct_cumplimiento_cop), fontWeight: 700 }}>{fmt(d.pct_cumplimiento_cop, 1)}%</span></div>
      <div style={{ color: '#94a3b8' }}>Ventas: <span style={{ color: '#e2e8f0' }}>{fmtCOP(d.ventas_cop)}</span></div>
      <div style={{ color: '#94a3b8' }}>Meta: <span style={{ color: '#e2e8f0' }}>{fmtCOP(d.meta_cop)}</span></div>
      <div style={{ color: '#94a3b8' }}>Tier: <span style={{ color: TIER_COLOR[d.tier] || '#fff' }}>{d.tier}</span></div>
    </div>
  )
}

// ── Página principal ──────────────────────────────────────────────
export default function CompliancePage() {
  const [data, setData]         = useState(null)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState(null)
  const [search, setSearch]     = useState('')
  const [tierFilter, setTier]   = useState('Todos')
  const [desde, setDesde]       = useState('')
  const [hasta, setHasta]       = useState('')
  const [activeTab, setTab]     = useState('ranking') // ranking | alertas | top

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getComplianceReport(desde || undefined, hasta || undefined)
      setData(res)
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || 'Error al cargar el informe')
    } finally {
      setLoading(false)
    }
  }, [desde, hasta])

  useEffect(() => { load() }, [load])

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 80 }}>
      <Spinner />
    </div>
  )

  if (error) return (
    <div style={{
      background: '#450a0a', border: '1px solid #ef4444', borderRadius: 10,
      padding: 20, color: '#fca5a5', marginTop: 20,
    }}>
      ⚠️ {error}
    </div>
  )

  if (!data) return null

  const { resumen_ejecutivo: ej, tiendas, top3, bottom3, alertas, periodo } = data

  // ── Datos para gráfica de barras ──────────────────────────────
  const chartData = [...tiendas]
    .sort((a, b) => b.pct_cumplimiento_cop - a.pct_cumplimiento_cop)
    .slice(0, 15)
    .map(t => ({
      name:                 t.tienda_nombre?.substring(0, 12) || `T${t.tienda_id}`,
      pct_cumplimiento_cop: t.pct_cumplimiento_cop,
      ventas_cop:           t.ventas_cop,
      meta_cop:             t.meta_cop,
      tier:                 t.tier,
    }))

  // ── Distribución de tiers para mini-stats ─────────────────────
  const tierDist = ej.distribucion_tiers || {}

  // ── Filtro de tabla ───────────────────────────────────────────
  const tiers = ['Todos', ...Object.keys(TIER_COLOR)]
  const filtered = tiendas.filter(t => {
    const matchSearch = search === '' ||
      t.tienda_nombre?.toLowerCase().includes(search.toLowerCase()) ||
      t.ciudad?.toLowerCase().includes(search.toLowerCase())
    const matchTier = tierFilter === 'Todos' || t.tier === tierFilter
    return matchSearch && matchTier
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* ── Filtros de período ───────────────────────────────────── */}
      <div style={{
        background: '#1e293b', borderRadius: 12, padding: '14px 20px',
        display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap',
      }}>
        <span style={{ color: '#94a3b8', fontSize: 13 }}>📅 Período:</span>
        <input
          type="date"
          value={desde}
          onChange={e => setDesde(e.target.value)}
          style={inputStyle}
          placeholder="Desde"
        />
        <input
          type="date"
          value={hasta}
          onChange={e => setHasta(e.target.value)}
          style={inputStyle}
          placeholder="Hasta"
        />
        <button onClick={load} style={btnStyle}>Actualizar</button>
        {(desde || hasta) && (
          <button onClick={() => { setDesde(''); setHasta('') }} style={{ ...btnStyle, background: '#334155' }}>
            Limpiar
          </button>
        )}
        <span style={{ color: '#64748b', fontSize: 12, marginLeft: 'auto' }}>
          {periodo.desde} → {periodo.hasta}
        </span>
      </div>

      {/* ── KPIs ─────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
        <KpiCard
          icon="🏪" label="Total tiendas" value={ej.total_tiendas}
          color="#3b82f6"
        />
        <KpiCard
          icon="🎯" label="Cumplimiento global"
          value={`${fmt(ej.cumplimiento_global_cop, 1)}%`}
          color={pctColor(ej.cumplimiento_global_cop)}
          sub="Promedio ponderado"
        />
        <KpiCard
          icon="✅" label="Sobre meta"
          value={ej.tiendas_sobre_meta}
          color="#22c55e"
          sub={`de ${ej.total_tiendas} tiendas`}
        />
        <KpiCard
          icon="⚠️" label="En riesgo (proy < 80%)"
          value={ej.tiendas_en_riesgo}
          color="#f59e0b"
        />
        <KpiCard
          icon="🔍" label="Tiendas anómalas"
          value={ej.tiendas_anomalas}
          color="#a855f7"
          sub="IsolationForest"
        />
        <KpiCard
          icon="💰" label="Ventas totales"
          value={fmtCOP(ej.total_ventas_cop)}
          color="#06b6d4"
          sub={`Meta: ${fmtCOP(ej.total_meta_cop)}`}
        />
        <KpiCard
          icon="📊" label="Ventas vs Meta"
          value={`${fmt(ej.pct_ventas_vs_meta, 1)}%`}
          color={pctColor(ej.pct_ventas_vs_meta)}
        />
      </div>

      {/* ── Distribución de tiers ─────────────────────────────────── */}
      <div style={{
        background: '#1e293b', borderRadius: 12, padding: '16px 20px',
      }}>
        <div style={{ fontSize: 13, color: '#94a3b8', marginBottom: 12, fontWeight: 600 }}>
          Distribución por Tier (KMeans)
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {Object.entries(TIER_COLOR).map(([tier, color]) => (
            <div key={tier} style={{
              background: color + '18', border: `1px solid ${color}`,
              borderRadius: 8, padding: '8px 16px', textAlign: 'center', minWidth: 110,
            }}>
              <div style={{ fontSize: 22, fontWeight: 700, color }}>{tierDist[tier] ?? 0}</div>
              <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>{tier}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Gráfica Top 15 tiendas ────────────────────────────────── */}
      <div style={{ background: '#1e293b', borderRadius: 12, padding: '20px 24px' }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: '#e2e8f0', marginBottom: 16 }}>
          Top 15 tiendas — Cumplimiento COP (%)
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ top: 0, right: 10, left: 0, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="name"
              tick={{ fill: '#94a3b8', fontSize: 10 }}
              angle={-35}
              textAnchor="end"
              interval={0}
            />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} unit="%" domain={[0, 'dataMax + 10']} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={100} stroke="#22c55e" strokeDasharray="4 4" label={{ value: 'Meta 100%', fill: '#22c55e', fontSize: 11 }} />
            <Bar dataKey="pct_cumplimiento_cop" radius={[4, 4, 0, 0]} maxBarSize={36}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={TIER_COLOR[entry.tier] || '#3b82f6'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ── Tabs: Ranking / Alertas / Top & Bottom ─────────────────── */}
      <div style={{ background: '#1e293b', borderRadius: 12, overflow: 'hidden' }}>
        {/* Tab bar */}
        <div style={{ display: 'flex', borderBottom: '1px solid #334155' }}>
          {[
            { id: 'ranking', label: `📋 Ranking (${filtered.length})` },
            { id: 'alertas', label: `🚨 Alertas (${alertas.length})` },
            { id: 'top',     label: '🏆 Top & Bottom' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setTab(tab.id)}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                padding: '12px 20px', fontSize: 13, fontWeight: 600,
                color: activeTab === tab.id ? '#3b82f6' : '#94a3b8',
                borderBottom: activeTab === tab.id ? '2px solid #3b82f6' : '2px solid transparent',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ── TAB: Ranking ───────────────────────────────────────────── */}
        {activeTab === 'ranking' && (
          <div style={{ padding: 20 }}>
            {/* Filtros */}
            <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
              <input
                type="text"
                placeholder="Buscar tienda o ciudad..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                style={{ ...inputStyle, flex: 1, minWidth: 200 }}
              />
              <select
                value={tierFilter}
                onChange={e => setTier(e.target.value)}
                style={inputStyle}
              >
                {tiers.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>

            {/* Tabla */}
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#0f172a' }}>
                    {['#', 'Tienda', 'Ciudad', 'Tier', 'Tendencia', 'Cump. %', 'Sem. %', 'Mes %', 'Proyec. %', 'Anómala'].map(h => (
                      <th key={h} style={thStyle}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((t, i) => (
                    <tr
                      key={t.tienda_id}
                      style={{
                        background: i % 2 === 0 ? '#1e293b' : '#172033',
                        borderBottom: '1px solid #334155',
                      }}
                    >
                      <td style={tdStyle}><span style={{ color: '#64748b' }}>{t.ranking}</span></td>
                      <td style={{ ...tdStyle, fontWeight: 600, color: '#e2e8f0' }}>{t.tienda_nombre}</td>
                      <td style={tdStyle}>{t.ciudad}</td>
                      <td style={tdStyle}><TierBadge tier={t.tier} /></td>
                      <td style={tdStyle}><TendBadge tendencia={t.tendencia} /></td>
                      <td style={{ ...tdStyle, fontWeight: 700, color: pctColor(t.pct_cumplimiento_cop) }}>
                        {fmt(t.pct_cumplimiento_cop, 1)}%
                      </td>
                      <td style={{ ...tdStyle, color: pctColor(t.pct_semanal) }}>
                        {fmt(t.pct_semanal, 1)}%
                      </td>
                      <td style={{ ...tdStyle, color: pctColor(t.pct_mensual) }}>
                        {fmt(t.pct_mensual, 1)}%
                      </td>
                      <td style={{ ...tdStyle, color: pctColor(t.pct_proyeccion) }}>
                        {fmt(t.pct_proyeccion, 1)}%
                      </td>
                      <td style={{ ...tdStyle, textAlign: 'center' }}>
                        {t.es_anomalia ? '⚠️' : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filtered.length === 0 && (
                <div style={{ textAlign: 'center', color: '#64748b', padding: 30 }}>
                  Sin resultados para los filtros aplicados
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── TAB: Alertas ──────────────────────────────────────────── */}
        {activeTab === 'alertas' && (
          <div style={{ padding: 20 }}>
            {alertas.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#22c55e', padding: 40, fontSize: 15 }}>
                ✅ Todas las tiendas tienen proyección ≥ 80% — Sin alertas activas
              </div>
            ) : (
              <>
                <div style={{ color: '#fca5a5', marginBottom: 16, fontSize: 13 }}>
                  ⚠️ {alertas.length} tienda{alertas.length !== 1 ? 's' : ''} con proyección mensual por debajo del 80%
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {alertas.map(t => (
                    <div key={t.tienda_id} style={{
                      background: '#1a0a0a', border: '1px solid #7f1d1d',
                      borderRadius: 10, padding: '14px 18px',
                      display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap',
                    }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 700, color: '#fca5a5' }}>
                          #{t.ranking} — {t.tienda_nombre}
                        </div>
                        <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>
                          {t.ciudad} · {t.region} · <TierBadge tier={t.tier} />
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: 20, fontWeight: 700, color: '#ef4444' }}>
                            {fmt(t.pct_proyeccion, 1)}%
                          </div>
                          <div style={{ fontSize: 10, color: '#94a3b8' }}>Proyección</div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: 20, fontWeight: 700, color: pctColor(t.pct_cumplimiento_cop) }}>
                            {fmt(t.pct_cumplimiento_cop, 1)}%
                          </div>
                          <div style={{ fontSize: 10, color: '#94a3b8' }}>Acumulado</div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: 14, fontWeight: 600 }}>
                            <TendBadge tendencia={t.tendencia} />
                          </div>
                          <div style={{ fontSize: 10, color: '#94a3b8' }}>Tendencia</div>
                        </div>
                        {t.es_anomalia && (
                          <div style={{
                            background: '#4c1d95', border: '1px solid #7c3aed',
                            borderRadius: 6, padding: '4px 10px', fontSize: 11, color: '#c4b5fd',
                            alignSelf: 'center',
                          }}>
                            🔍 Comportamiento anómalo
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* ── TAB: Top & Bottom ─────────────────────────────────────── */}
        {activeTab === 'top' && (
          <div style={{ padding: 20, display: 'flex', gap: 20, flexWrap: 'wrap' }}>
            {/* Top 3 */}
            <div style={{ flex: 1, minWidth: 280 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#22c55e', marginBottom: 14 }}>
                🏆 Top 3 — Mejores tiendas
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {top3.map((t, i) => (
                  <TopCard key={t.tienda_id} t={t} rank={i + 1} variant="top" />
                ))}
              </div>
            </div>

            {/* Bottom 3 */}
            <div style={{ flex: 1, minWidth: 280 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#ef4444', marginBottom: 14 }}>
                🚨 Bottom 3 — Tiendas rezagadas
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {bottom3.map((t, i) => (
                  <TopCard key={t.tienda_id} t={t} rank={tiendas.length - 2 + i} variant="bottom" />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Tarjeta Top/Bottom ─────────────────────────────────────────────
function TopCard({ t, rank, variant }) {
  const accent = variant === 'top' ? '#22c55e' : '#ef4444'
  return (
    <div style={{
      background: '#0f172a', border: `1px solid ${accent}44`,
      borderRadius: 10, padding: '14px 18px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontWeight: 700, color: '#e2e8f0', fontSize: 14 }}>
            #{rank} {t.tienda_nombre}
          </div>
          <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>
            {t.ciudad} · {t.formato}
          </div>
          <div style={{ marginTop: 6 }}><TierBadge tier={t.tier} /></div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 24, fontWeight: 800, color: accent }}>
            {Number(t.pct_cumplimiento_cop).toLocaleString('es-CO', { maximumFractionDigits: 1 })}%
          </div>
          <div style={{ fontSize: 10, color: '#64748b' }}>cumplimiento</div>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 16, marginTop: 12, fontSize: 12, color: '#94a3b8' }}>
        <span>Proy: <b style={{ color: pctColor(t.pct_proyeccion) }}>{Number(t.pct_proyeccion).toFixed(1)}%</b></span>
        <span>Días s/meta: <b style={{ color: '#e2e8f0' }}>{t.dias_sobre_meta}</b></span>
        <span><TendBadge tendencia={t.tendencia} /></span>
      </div>
    </div>
  )
}

// ── Estilos reutilizables ──────────────────────────────────────────
const inputStyle = {
  background: '#0f172a', border: '1px solid #334155', borderRadius: 8,
  color: '#e2e8f0', padding: '7px 12px', fontSize: 13, outline: 'none',
}

const btnStyle = {
  background: '#3b82f6', border: 'none', borderRadius: 8,
  color: '#fff', padding: '7px 16px', fontSize: 13,
  fontWeight: 600, cursor: 'pointer',
}

const thStyle = {
  padding: '10px 12px', textAlign: 'left', fontSize: 12,
  color: '#64748b', fontWeight: 600, whiteSpace: 'nowrap',
}

const tdStyle = {
  padding: '10px 12px', color: '#cbd5e1', verticalAlign: 'middle',
}
