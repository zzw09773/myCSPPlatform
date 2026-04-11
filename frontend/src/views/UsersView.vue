<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold">使用者管理</h2>
      <button
        @click="openCreateModal"
        class="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 transition"
      >
        新增使用者
      </button>
    </div>

    <!-- Users Table -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="px-4 py-3 text-left text-gray-600 font-medium">帳號</th>
            <th class="px-4 py-3 text-left text-gray-600 font-medium">Email</th>
            <th class="px-4 py-3 text-left text-gray-600 font-medium">角色</th>
            <th class="px-4 py-3 text-left text-gray-600 font-medium">狀態</th>
            <th class="px-4 py-3 text-left text-gray-600 font-medium">建立日期</th>
            <th class="px-4 py-3 text-left text-gray-600 font-medium">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id" class="border-b last:border-0 hover:bg-gray-50">
            <td class="px-4 py-3 font-medium">{{ user.username }}</td>
            <td class="px-4 py-3 text-gray-500">{{ user.email || '-' }}</td>
            <td class="px-4 py-3">
              <span
                class="text-xs px-2 py-0.5 rounded"
                :class="user.role === 'admin' ? 'bg-purple-50 text-purple-700' : 'bg-gray-100 text-gray-600'"
              >
                {{ user.role === 'admin' ? '管理員' : '使用者' }}
              </span>
            </td>
            <td class="px-4 py-3">
              <span
                class="text-xs px-2 py-0.5 rounded"
                :class="user.is_active ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'"
              >
                {{ user.is_active ? '啟用' : '停用' }}
              </span>
            </td>
            <td class="px-4 py-3 text-gray-500">{{ formatDate(user.created_at) }}</td>
            <td class="px-4 py-3 space-x-2">
              <button @click="openEditModal(user)" class="text-indigo-600 hover:text-indigo-800 text-xs">
                編輯
              </button>
              <button @click="openResetPasswordModal(user)" class="text-orange-600 hover:text-orange-800 text-xs">
                重設密碼
              </button>
              <button
                v-if="user.is_active"
                @click="handleDeactivate(user)"
                class="text-red-600 hover:text-red-800 text-xs"
              >
                停用
              </button>
            </td>
          </tr>
          <tr v-if="users.length === 0">
            <td colspan="6" class="px-4 py-8 text-center text-gray-400">尚無使用者</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="fixed inset-0 bg-black/50" @click="showModal = false"></div>
      <div class="relative bg-white rounded-xl shadow-xl p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-semibold mb-4">{{ editingId ? '編輯使用者' : '新增使用者' }}</h3>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">帳號</label>
            <input v-model="form.username" :disabled="!!editingId" type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 disabled:bg-gray-100"
              placeholder="帳號" />
          </div>
          <div v-if="!editingId">
            <label class="block text-sm font-medium text-gray-700 mb-1">密碼</label>
            <input v-model="form.password" type="password"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="密碼" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input v-model="form.email" type="email"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="選填" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">角色</label>
            <select v-model="form.role"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500">
              <option value="user">使用者</option>
              <option value="admin">管理員</option>
            </select>
          </div>
        </div>

        <div class="flex justify-end space-x-3 mt-6">
          <button @click="showModal = false"
            class="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
            取消
          </button>
          <button @click="handleSubmit"
            :disabled="!form.username || (!editingId && !form.password)"
            class="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50">
            {{ editingId ? '更新' : '建立' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Reset Password Modal -->
    <div v-if="showResetModal" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="fixed inset-0 bg-black/50" @click="showResetModal = false"></div>
      <div class="relative bg-white rounded-xl shadow-xl p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-semibold mb-4">重設密碼 — {{ resetTarget?.username }}</h3>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">新密碼</label>
            <input v-model="resetPassword" type="password"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-orange-500"
              placeholder="請輸入新密碼" />
          </div>
        </div>

        <div class="flex justify-end space-x-3 mt-6">
          <button @click="showResetModal = false"
            class="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
            取消
          </button>
          <button @click="handleResetPassword"
            :disabled="!resetPassword"
            class="px-4 py-2 text-sm bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50">
            確認重設
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import client from '../api/client'

const users = ref([])
const showModal = ref(false)
const editingId = ref(null)
const form = ref({ username: '', password: '', email: '', role: 'user' })
const showResetModal = ref(false)
const resetTarget = ref(null)
const resetPassword = ref('')

async function fetchUsers() {
  const { data } = await client.get('/api/users')
  users.value = data
}

onMounted(fetchUsers)

function openCreateModal() {
  editingId.value = null
  form.value = { username: '', password: '', email: '', role: 'user' }
  showModal.value = true
}

function openEditModal(user) {
  editingId.value = user.id
  form.value = { username: user.username, email: user.email || '', role: user.role }
  showModal.value = true
}

async function handleSubmit() {
  try {
    if (editingId.value) {
      await client.put(`/api/users/${editingId.value}`, {
        email: form.value.email || null,
        role: form.value.role,
      })
    } else {
      await client.post('/api/users', form.value)
    }
    showModal.value = false
    await fetchUsers()
  } catch (e) {
    alert(e.response?.data?.detail || '操作失敗')
  }
}

function openResetPasswordModal(user) {
  resetTarget.value = user
  resetPassword.value = ''
  showResetModal.value = true
}

async function handleResetPassword() {
  try {
    await client.post(`/api/users/${resetTarget.value.id}/reset-password`, {
      new_password: resetPassword.value,
    })
    showResetModal.value = false
    alert(`已重設使用者「${resetTarget.value.username}」的密碼`)
  } catch (e) {
    alert(e.response?.data?.detail || '重設密碼失敗')
  }
}

async function handleDeactivate(user) {
  if (confirm(`確定要停用使用者「${user.username}」嗎？`)) {
    await client.delete(`/api/users/${user.id}`)
    await fetchUsers()
  }
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleString('zh-TW')
}
</script>
