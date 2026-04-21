import client from './client'
import axios from 'axios'

// ── Auth ─────────────────────────────────────────────────────────

export const login = async (username, password) => {
  // OAuth2 requires form-urlencoded
  const params = new URLSearchParams()
  params.append('username', username)
  params.append('password', password)
  const { data } = await axios.post('/api/v1/auth/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

export const getMe = () => client.get('/auth/me').then(r => r.data)

// ── Demand ───────────────────────────────────────────────────────

export const getForecasts = (params = {}) =>
  client.get('/demand/forecasts', { params }).then(r => r.data)

export const getPredictions = (params = {}) =>
  client.get('/demand/predictions', { params }).then(r => r.data)

export const runProphet = () =>
  client.post('/demand/run/prophet').then(r => r.data)

export const runLightGBM = () =>
  client.post('/demand/run/lightgbm').then(r => r.data)

// ── Inventory ────────────────────────────────────────────────────

export const getAnomalies = (params = {}) =>
  client.get('/inventory/anomalies', { params }).then(r => r.data)

export const getEOQ = (params = {}) =>
  client.get('/inventory/eoq', { params }).then(r => r.data)

export const getMonteCarlo = (params = {}) =>
  client.get('/inventory/monte-carlo', { params }).then(r => r.data)

export const runAnomalies = () =>
  client.post('/inventory/run/anomalies').then(r => r.data)

export const runEOQ = () =>
  client.post('/inventory/run/eoq').then(r => r.data)

export const runMonteCarlo = () =>
  client.post('/inventory/run/monte-carlo').then(r => r.data)

// ── Analytics ────────────────────────────────────────────────────

export const getRentability = (params = {}) =>
  client.get('/analytics/rentability', { params }).then(r => r.data)

export const getRotation = (params = {}) =>
  client.get('/analytics/rotation', { params }).then(r => r.data)

export const getEfficiency = (params = {}) =>
  client.get('/analytics/efficiency', { params }).then(r => r.data)

export const runRentability = () =>
  client.post('/analytics/run/rentability').then(r => r.data)

export const runRotation = () =>
  client.post('/analytics/run/rotation').then(r => r.data)

export const runEfficiency = () =>
  client.post('/analytics/run/efficiency').then(r => r.data)

// ── Products ─────────────────────────────────────────────────────

export const getProducts = (params = {}) =>
  client.get('/products', { params }).then(r => r.data)

export const getSegmentation = (params = {}) =>
  client.get('/products/segmentation/abc', { params }).then(r => r.data)

export const getMarketBasket = (params = {}) =>
  client.get('/products/market-basket/rules', { params }).then(r => r.data)

export const runSegmentation = () =>
  client.post('/products/run/segmentation').then(r => r.data)

export const runMarketBasket = () =>
  client.post('/products/run/market-basket').then(r => r.data)

// ── Stores ───────────────────────────────────────────────────────

export const getStores = () =>
  client.get('/stores').then(r => r.data)

export const getStoreSegmentation = () =>
  client.get('/stores/segmentation/clusters').then(r => r.data)

// ── Admin ────────────────────────────────────────────────────────

export const runAllModels = () =>
  client.post('/admin/run-all-models').then(r => r.data)
