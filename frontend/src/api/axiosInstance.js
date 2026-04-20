// src/api/axiosInstance.js

import axios from 'axios'

// ─────────────────────────────────────────────
// BASE AXIOS INSTANCE
//
// All API calls go through this instance.
// withCredentials: true ensures httpOnly cookies
// (access_token, refresh_token) are automatically
// sent with every request — no manual token
// handling needed.
// ─────────────────────────────────────────────
const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─────────────────────────────────────────────
// RESPONSE INTERCEPTOR — Silent Token Refresh
//
// When the access token expires, Django returns
// a 401. This interceptor:
// 1. Catches the 401
// 2. Attempts a silent token refresh using the
//    refresh cookie
// 3. Retries the original request once
// 4. If refresh also fails, clears auth state
//    and redirects to login
//
// The _retry flag prevents infinite retry loops
// if the refresh endpoint itself returns 401.
// ─────────────────────────────────────────────
api.interceptors.response.use(
  // Pass successful responses straight through
  (response) => response,

  async (error) => {
    const originalRequest = error.config

    // Only attempt refresh on 401 and only once
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // Attempt silent refresh — reads refresh cookie automatically
        await axios.post(
          '/api/v1/auth/token/refresh/',
          {},
          { withCredentials: true }
        )

        // Refresh succeeded — retry the original request
        // The new access cookie is now set, so this will work
        return api(originalRequest)

      } catch (refreshError) {
        // Refresh failed — user's session is truly expired
        // Redirect to login so they can authenticate again
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api