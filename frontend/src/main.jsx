// src/main.jsx

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'

import store from './store/index'
import router from './router'
import './index.css'

// ─────────────────────────────────────────────
// TANSTACK QUERY CLIENT
//
// Global configuration for all server data fetching.
// retry: 1 — retry failed requests once before showing error
// staleTime — how long cached data is considered fresh
// ─────────────────────────────────────────────
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry:              1,
      staleTime:          1000 * 60 * 5,   // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
})

// ─────────────────────────────────────────────
// APP INITIALIZER
//
// Dispatches initializeAuth on startup to restore
// auth state from the httpOnly access cookie.
// This runs once when the app first loads.
// ─────────────────────────────────────────────
import { initializeAuth } from './store/authSlice'
store.dispatch(initializeAuth())

// ─────────────────────────────────────────────
// ROOT RENDER
// ─────────────────────────────────────────────
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#1e293b',
              color:      '#e2e8f0',
              border:     '1px solid #334155',
              borderRadius: '10px',
              fontSize:   '14px',
            },
            success: {
              iconTheme: {
                primary: '#8b5cf6',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#f87171',
                secondary: '#fff',
              },
            },
          }}
        />
      </QueryClientProvider>
    </Provider>
  </StrictMode>
)