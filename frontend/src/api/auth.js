import client from './client'

export const login = (username, password) =>
  client.post('/api/auth/login', { username, password })

export const refreshTokenApi = (refresh_token) =>
  client.post('/api/auth/refresh', { refresh_token })

export const getMe = () =>
  client.get('/api/auth/me')

export const changePassword = (current_password, new_password) =>
  client.put('/api/auth/password', { current_password, new_password })
