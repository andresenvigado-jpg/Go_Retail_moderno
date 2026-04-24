import client from './client'
import axios from 'axios'

const BASE_URL = 'https://go-retail-moderno.onrender.com/api/v1'

// ── Auth ─────────────────────────────────────────────────────────
export const login = async (username, password) => {
  const params = new URLSearchParams()
  params.append('username', username)
  params.append('password', password)
  const { data } = await axios.post(`${BASE_URL}/auth/login`, params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

export const getMe = async () => {
  const { data } = await client.get('/auth/me')
  return data
}

// ── Inventario ────────────────────────────────────────────────────
export const getAnomalies    = () => client.get('/inventory/anomalies').then(r => r.data)
export const getEOQ          = () => client.get('/inventory/eoq').then(r => r.data)
export const getMonteCarlo   = () => client.get('/inventory/monte-carlo').then(r => r.data)
export const runAnomalies    = () => client.post('/inventory/run/anomalies').then(r => r.data)
export const runEOQ          = () => client.post('/inventory/run/eoq').then(r => r.data)
export const runMonteCarlo   = () => client.post('/inventory/run/monte-carlo').then(r => r.data)

// ── Demanda ───────────────────────────────────────────────────────
export const getForecasts    = () => client.get('/demand/forecasts').then(r => r.data)
export const getPredictions  = () => client.get('/demand/predictions').then(r => r.data)
export const runForecast     = () => client.post('/demand/run/forecast').then(r => r.data)
export const runLGBM         = () => client.post('/demand/run/lgbm').then(r => r.data)
export const runLightGBM     = () => client.post('/demand/run/lgbm').then(r => r.data)

// ── Analítica ─────────────────────────────────────────────────────
export const getRentability  = () => client.get('/analytics/rentability').then(r => r.data)
export const getRotation     = () => client.get('/analytics/rotation').then(r => r.data)
export const getEfficiency   = () => client.get('/analytics/efficiency').then(r => r.data)
export const runRentability  = () => client.post('/analytics/run/rentability').then(r => r.data)
export const runRotation     = () => client.post('/analytics/run/rotation').then(r => r.data)
export const runEfficiency   = () => client.post('/analytics/run/efficiency').then(r => r.data)

// ── Productos ─────────────────────────────────────────────────────
export const getProducts       = () => client.get('/products').then(r => r.data)
export const getSegmentation   = () => client.get('/products/segmentation/abc').then(r => r.data)
export const getMarketBasket   = () => client.get('/products/market-basket/rules').then(r => r.data)
export const runSegmentation   = () => client.post('/products/run/segmentation').then(r => r.data)
export const runMarketBasket   = () => client.post('/products/run/market-basket').then(r => r.data)

// ── Tiendas ───────────────────────────────────────────────────────
export const getStores             = () => client.get('/stores').then(r => r.data)
export const getStoreSegmentation  = () => client.get('/products/segmentation/abc').then(r => r.data)

// ── Cumplimiento ──────────────────────────────────────────────────
export const getComplianceReport = (desde, hasta) => {
  const params = {}
  if (desde) params.fecha_desde = desde
  if (hasta) params.fecha_hasta = hasta
  return client.get('/compliance/report', { params }).then(r => r.data)
}