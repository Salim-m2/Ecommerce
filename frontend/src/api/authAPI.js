// src/api/authAPI.js

import api from './axiosInstance'

// ─────────────────────────────────────────────
// AUTH API FUNCTIONS
//
// These functions wrap all authentication-related
// API calls. All use the shared axios instance
// so cookies are sent automatically.
// ─────────────────────────────────────────────

// Register a new user account
export const register = (data) =>
  api.post('/auth/register/', data)

// Login — sets httpOnly JWT cookies on success
export const login = (data) =>
  api.post('/auth/login/', data)

// Logout — clears both JWT cookies server-side
export const logout = () =>
  api.post('/auth/logout/')

// Silent token refresh — reads refresh cookie,
// issues a new access cookie
export const refreshToken = () =>
  api.post('/auth/token/refresh/')

// Get the currently authenticated user
// Used on app startup to restore auth state
export const getMe = () =>
  api.get('/auth/me/')

// Request a password reset email
export const requestPasswordReset = (email) =>
  api.post('/auth/password/reset/', { email })

// Confirm password reset with token + new password
export const confirmPasswordReset = (token, newPassword) =>
  api.post('/auth/password/reset/confirm/', {
    token,
    new_password: newPassword,
  })