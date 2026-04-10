import client from './client'

export const getUsageSummary = (params) =>
  client.get('/api/usage/summary', { params })

export const getUsageChart = (params) =>
  client.get('/api/usage/chart', { params })

export const getTopModels = (params) =>
  client.get('/api/usage/top-models', { params })

export const getTopUsers = (limit = 10) =>
  client.get('/api/usage/top-users', { params: { limit } })

export const exportUsageCsv = (params) =>
  client.get('/api/usage/export', { params, responseType: 'blob' })
