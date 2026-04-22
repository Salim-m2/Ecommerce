import { StrictMode, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { Provider, useDispatch } from 'react-redux'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'

import store from './store'
import router from './router'
import { initializeAuth } from './store/authSlice'
import './index.css'

// ─────────────────────────────────────────────
// TANSTACK QUERY CLIENT
// ─────────────────────────────────────────────
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 1000 * 60 * 5,
      refetchOnWindowFocus: false,
    },
  },
})

// ─────────────────────────────────────────────
// AUTH INITIALIZER COMPONENT
// ─────────────────────────────────────────────
const AppInitializer = ({ children }) => {
  const dispatch = useDispatch()

  useEffect(() => {
    dispatch(initializeAuth())
  }, [dispatch])

  return children
}

// ─────────────────────────────────────────────
// ROOT RENDER
// ─────────────────────────────────────────────
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        
        <AppInitializer>
          <RouterProvider router={router} />
        </AppInitializer>

        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#1e293b',
              color: '#e2e8f0',
              border: '1px solid #334155',
              borderRadius: '10px',
              fontSize: '14px',
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