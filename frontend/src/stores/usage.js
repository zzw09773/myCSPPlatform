import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getUsageSummary, getUsageChart, getTopModels, getTopUsers, exportUsageCsv } from '../api/usage'

export const useUsageStore = defineStore('usage', () => {
  const summary = ref(null)
  const chartData = ref(null)
  const topModels = ref([])
  const topUsers = ref([])
  const loading = ref(false)

  async function fetchSummary() {
    const { data } = await getUsageSummary()
    summary.value = data
  }

  async function fetchChart(params) {
    loading.value = true
    try {
      const { data } = await getUsageChart(params)
      chartData.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchTopModels(limit = 10) {
    const { data } = await getTopModels(limit)
    topModels.value = data
  }

  async function fetchTopUsers(limit = 10) {
    const { data } = await getTopUsers(limit)
    topUsers.value = data
  }

  async function exportCsv(params) {
    const { data } = await exportUsageCsv(params)
    const blob = new Blob([data], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `usage_${params.range || '24h'}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  return {
    summary, chartData, topModels, topUsers, loading,
    fetchSummary, fetchChart, fetchTopModels, fetchTopUsers, exportCsv,
  }
})
