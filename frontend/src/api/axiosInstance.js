// src/api/axiosInstance.js

import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─────────────────────────────────────────────
// URLS that should never trigger a token refresh retry
// ─────────────────────────────────────────────
const SKIP_REFRESH_URLS = [
  '/auth/me/',
  '/auth/token/refresh/',
  '/auth/login/',
  '/auth/logout/',
]

api.interceptors.response.use(
  (response) => response,

  async (error) => {
    const originalRequest = error.config
    const requestUrl = originalRequest?.url || ''

    // Skip refresh logic for auth endpoints and already-retried requests
    const shouldSkip = SKIP_REFRESH_URLS.some(url => requestUrl.includes(url))

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !shouldSkip
    ) {
      originalRequest._retry = true

      try {
        await axios.post(
          '/api/v1/auth/token/refresh/',
          {},
          { withCredentials: true }
        )
        return api(originalRequest)

      } catch (refreshError) {
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api