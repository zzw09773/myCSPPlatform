import client from './client'

export const getUsageSummary = () =>
  client.get('/api/usage/summary')

export const getUsageChart = (params) =>
  client.get('/api/usage/chart', { params })

export const getTopModels = (limit = 10) =>
  client.get('/api/usage/top-models', { params: { limit } })

export const getTopUsers = (limit = 10) =>
  client.get('/api/usage/top-users', { params: { limit } })

export const exportUsageCsv = (params) =>
  client.get('/api/usage/export', { params, responseType: 'blob' })
