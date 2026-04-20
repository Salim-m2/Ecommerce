// src/store/authSlice.js

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { login, register, logout, getMe } from '../api/authAPI'

// ─────────────────────────────────────────────
// ASYNC THUNKS
//
// These handle API calls and automatically
// dispatch pending/fulfilled/rejected actions
// ─────────────────────────────────────────────

// Login — sends credentials, sets cookies server-side
export const loginUser = createAsyncThunk(
  'auth/loginUser',
  async (credentials, { rejectWithValue }) => {
    try {
      const response = await login(credentials)
      return response.data.user
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.error ||
        error.response?.data ||
        'Login failed. Please try again.'
      )
    }
  }
)

// Register — creates account
export const registerUser = createAsyncThunk(
  'auth/registerUser',
  async (data, { rejectWithValue }) => {
    try {
      const response = await register(data)
      return response.data.user
    } catch (error) {
      return rejectWithValue(
        error.response?.data ||
        'Registration failed. Please try again.'
      )
    }
  }
)

// Logout — clears cookies server-side
export const logoutUser = createAsyncThunk(
  'auth/logoutUser',
  async (_, { rejectWithValue }) => {
    try {
      await logout()
    } catch (error) {
      return rejectWithValue('Logout failed.')
    }
  }
)

// Initialize auth — called on app startup to
// restore user state from the access cookie
export const initializeAuth = createAsyncThunk(
  'auth/initializeAuth',
  async (_, { rejectWithValue }) => {
    try {
      const response = await getMe()
      return response.data
    } catch (error) {
      // 401 means no valid cookie — user is not logged in
      // This is not an error — just means they need to login
      return rejectWithValue(null)
    }
  }
)

// ─────────────────────────────────────────────
// INITIAL STATE
// ─────────────────────────────────────────────
const initialState = {
  user:            null,
  isAuthenticated: false,
  isLoading:       false,
  isInitialized:   false,   // true after initializeAuth completes
  error:           null,
}

// ─────────────────────────────────────────────
// SLICE
// ─────────────────────────────────────────────
const authSlice = createSlice({
  name: 'auth',
  initialState,

  reducers: {
    // Clear any auth errors (e.g. when user starts typing again)
    clearError: (state) => {
      state.error = null
    },
  },

  extraReducers: (builder) => {
    // ── loginUser ──────────────────────────
    builder
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true
        state.error     = null
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.isLoading      = false
        state.isAuthenticated = true
        state.user           = action.payload
        state.error          = null
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading      = false
        state.isAuthenticated = false
        state.user           = null
        state.error          = action.payload
      })

    // ── registerUser ───────────────────────
    builder
      .addCase(registerUser.pending, (state) => {
        state.isLoading = true
        state.error     = null
      })
      .addCase(registerUser.fulfilled, (state) => {
        state.isLoading = false
        state.error     = null
        // Don't set isAuthenticated — user must login after registering
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.isLoading = false
        state.error     = action.payload
      })

    // ── logoutUser ─────────────────────────
    builder
      .addCase(logoutUser.pending, (state) => {
        state.isLoading = true
      })
      .addCase(logoutUser.fulfilled, (state) => {
        state.isLoading      = false
        state.isAuthenticated = false
        state.user           = null
        state.error          = null
      })
      .addCase(logoutUser.rejected, (state) => {
        // Even if logout API fails, clear local state
        state.isLoading      = false
        state.isAuthenticated = false
        state.user           = null
      })

    // ── initializeAuth ─────────────────────
    builder
      .addCase(initializeAuth.pending, (state) => {
        state.isLoading    = true
        state.isInitialized = false
      })
      .addCase(initializeAuth.fulfilled, (state, action) => {
        state.isLoading      = false
        state.isInitialized  = true
        state.isAuthenticated = true
        state.user           = action.payload
      })
      .addCase(initializeAuth.rejected, (state) => {
        state.isLoading      = false
        state.isInitialized  = true
        state.isAuthenticated = false
        state.user           = null
      })
  },
})

export const { clearError } = authSlice.actions

// ─────────────────────────────────────────────
// SELECTORS
// ─────────────────────────────────────────────
export const selectCurrentUser      = (state) => state.auth.user
export const selectIsAuthenticated  = (state) => state.auth.isAuthenticated
export const selectAuthLoading      = (state) => state.auth.isLoading
export const selectAuthError        = (state) => state.auth.error
export const selectIsInitialized    = (state) => state.auth.isInitialized

export default authSlice.reducer