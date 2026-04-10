<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between flex-wrap gap-4">
      <h2 class="text-lg font-semibold">用量分析</h2>
      <div class="flex items-center space-x-4">
        <TimeRangeSelector v-model="selectedRange" @update:model-value="loadChart" />
        <button
          @click="handleExport"
          class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50"
        >
          匯出 CSV
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex items-center space-x-4 flex-wrap gap-2">
      <div>
        <label class="text-sm text-gray-600 mr-2">模型：</label>
        <select
          v-model="selectedModel"
          @change="loadChart"
          class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option :value="null">全部</option>
          <option v-for="m in models" :key="m.id" :value="m.id">{{ m.display_name }}</option>
        </select>
      </div>
      <div v-if="authStore.isAdmin">
        <label class="text-sm text-gray-600 mr-2">使用者：</label>
        <select
          v-model="selectedUser"
          @change="loadChart"
          class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option :value="null">全部</option>
          <option v-for="u in users" :key="u.id" :value="u.id">{{ u.username }}</option>
        </select>
      </div>
      <div>
        <label class="text-sm text-gray-600 mr-2">分組：</label>
        <select
          v-model="groupBy"
          @change="loadChart"
          class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="total">總計</option>
          <option value="model">依模型</option>
          <option v-if="authStore.isAdmin" value="user">依使用者</option>
        </select>
      </div>
    </div>

    <!-- Chart -->
    <div class="bg-white rounded-xl border border-gray-200 p-5">
      <UsageLineChart :chart-data="usageStore.chartData" :height="400" />
    </div>

    <!-- Top Models & Users -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white rounded-xl border border-gray-200 p-5">
        <h3 class="text-sm font-medium text-gray-700 mb-3">Top 模型用量（30 天）</h3>
        <table class="w-full text-sm">
          <thead>
            <tr class="text-gray-500 border-b">
              <th class="py-2 text-left">模型</th>
              <th class="py-2 text-right">Token 數</th>
              <th class="py-2 text-right">請求數</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in usageStore.topModels" :key="m.model_id" class="border-b last:border-0">
              <td class="py-2">{{ m.model_name }}</td>
              <td class="py-2 text-right font-mono">{{ formatNum(m.total_tokens) }}</td>
              <td class="py-2 text-right font-mono">{{ formatNum(m.total_requests) }}</td>
            </tr>
            <tr v-if="usageStore.topModels.length === 0">
              <td colspan="3" class="py-4 text-center text-gray-400">暫無資料</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="authStore.isAdmin" class="bg-white rounded-xl border border-gray-200 p-5">
        <h3 class="text-sm font-medium text-gray-700 mb-3">Top 使用者用量（30 天）</h3>
        <table class="w-full text-sm">
          <thead>
            <tr class="text-gray-500 border-b">
              <th class="py-2 text-left">使用者</th>
              <th class="py-2 text-right">Token 數</th>
              <th class="py-2 text-right">請求數</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in usageStore.topUsers" :key="u.user_id" class="border-b last:border-0">
              <td class="py-2">{{ u.username }}</td>
              <td class="py-2 text-right font-mono">{{ formatNum(u.total_tokens) }}</td>
              <td class="py-2 text-right font-mono">{{ formatNum(u.total_requests) }}</td>
            </tr>
            <tr v-if="usageStore.topUsers.length === 0">
              <td colspan="3" class="py-4 text-center text-gray-400">暫無資料</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUsageStore } from '../stores/usage'
import { useAuthStore } from '../stores/auth'
import { listModels } from '../api/models'
import UsageLineChart from '../components/charts/UsageLineChart.vue'
import TimeRangeSelector from '../components/charts/TimeRangeSelector.vue'
import client from '../api/client'

const usageStore = useUsageStore()
const authStore = useAuthStore()

const selectedRange = ref('24h')
const selectedModel = ref(null)
const selectedUser = ref(null)
const groupBy = ref('total')
const models = ref([])
const users = ref([])

onMounted(async () => {
  try {
    const { data } = await listModels()
    models.value = data
  } catch {}

  if (authStore.isAdmin) {
    try {
      const { data } = await client.get('/api/users')
      users.value = data
    } catch {}
  }

  await loadChart()
  await usageStore.fetchTopModels()
  if (authStore.isAdmin) await usageStore.fetchTopUsers()
})

async function loadChart() {
  await usageStore.fetchChart({
    range: selectedRange.value,
    model_id: selectedModel.value || undefined,
    user_id: selectedUser.value || undefined,
    group_by: groupBy.value,
  })
}

function handleExport() {
  usageStore.exportCsv({
    range: selectedRange.value,
    model_id: selectedModel.value || undefined,
    user_id: selectedUser.value || undefined,
  })
}

function formatNum(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return n.toLocaleString()
}
</script>
