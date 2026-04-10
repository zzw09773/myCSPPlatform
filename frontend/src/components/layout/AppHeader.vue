<template>
  <header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
    <h2 class="text-lg font-semibold text-gray-800">{{ pageTitle }}</h2>
    <div class="flex items-center space-x-4">
      <span class="text-sm text-gray-500">{{ authStore.user?.username }}</span>
      <button
        @click="handleLogout"
        class="text-sm text-gray-500 hover:text-red-600 transition-colors"
      >
        登出
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const pageTitles = {
  '/': '儀表板',
  '/api-keys': 'API Key 管理',
  '/models': '模型管理',
  '/usage': '用量分析',
  '/users': '使用者管理',
}

const pageTitle = computed(() => pageTitles[route.path] || 'CSP Platform')

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>
