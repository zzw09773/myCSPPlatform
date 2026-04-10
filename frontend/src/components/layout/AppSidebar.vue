<template>
  <aside class="w-64 bg-gray-900 text-white min-h-screen flex flex-col">
    <div class="p-6 border-b border-gray-700">
      <h1 class="text-xl font-bold">CSP Platform</h1>
      <p class="text-gray-400 text-sm mt-1">AI 模型服務管理</p>
    </div>

    <nav class="flex-1 p-4 space-y-1">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="flex items-center px-4 py-3 rounded-lg text-sm transition-colors"
        :class="$route.path === item.path
          ? 'bg-indigo-600 text-white'
          : 'text-gray-300 hover:bg-gray-800 hover:text-white'"
      >
        <span class="mr-3 text-lg" v-html="item.icon"></span>
        {{ item.label }}
      </router-link>
    </nav>

    <div class="p-4 border-t border-gray-700">
      <div class="text-sm text-gray-400">
        {{ authStore.user?.username }}
        <span class="ml-1 text-xs px-2 py-0.5 rounded bg-gray-700">
          {{ authStore.user?.role === 'admin' ? '管理員' : '使用者' }}
        </span>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()

const menuItems = computed(() => {
  const items = [
    { path: '/', label: '儀表板', icon: '&#9633;' },
    { path: '/api-keys', label: 'API Key 管理', icon: '&#128273;' },
    { path: '/models', label: '模型管理', icon: '&#9881;' },
    { path: '/usage', label: '用量分析', icon: '&#128200;' },
  ]
  if (authStore.isAdmin) {
    items.push({ path: '/users', label: '使用者管理', icon: '&#128101;' })
  }
  return items
})
</script>
