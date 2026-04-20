// src/router.jsx

import { createBrowserRouter, Outlet, Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import {
  selectIsAuthenticated,
  selectIsInitialized,
} from './store/authSlice'

import Navbar   from './components/layout/Navbar'
import Footer   from './components/layout/Footer'
import Spinner  from './components/ui/Spinner'

import Home            from './pages/Home'
import Login           from './pages/auth/Login'
import Register        from './pages/auth/Register'
import ForgotPassword  from './pages/auth/ForgotPassword'

// ─────────────────────────────────────────────
// ROOT LAYOUT
//
// Wraps every page with Navbar + Footer.
// Outlet renders the current route's component.
// ─────────────────────────────────────────────
const RootLayout = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}

// ─────────────────────────────────────────────
// PROTECTED ROUTE
//
// Waits for auth to initialize (page refresh),
// then redirects to /login if not authenticated.
// Shows a spinner while initializing so there
// is no flash of unauthenticated content.
// ─────────────────────────────────────────────
const ProtectedRoute = () => {
  const isAuthenticated = useSelector(selectIsAuthenticated)
  const isInitialized   = useSelector(selectIsInitialized)

  // Still checking auth status — show spinner
  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  // Not authenticated — redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // Authenticated — render the protected page
  return <Outlet />
}

// ─────────────────────────────────────────────
// GUEST ONLY ROUTE
//
// Redirects authenticated users away from
// login/register pages back to home.
// ─────────────────────────────────────────────
const GuestRoute = () => {
  const isAuthenticated = useSelector(selectIsAuthenticated)
  const isInitialized   = useSelector(selectIsInitialized)

  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}

// ─────────────────────────────────────────────
// ROUTER CONFIGURATION
// ─────────────────────────────────────────────
const router = createBrowserRouter([
  {
    // Root layout wraps all routes
    element: <RootLayout />,
    children: [

      // ── Public routes ──────────────────────
      {
        path: '/',
        element: <Home />,
      },

      // ── Guest only routes ──────────────────
      // (redirect to / if already logged in)
      {
        element: <GuestRoute />,
        children: [
          { path: '/login',           element: <Login /> },
          { path: '/register',        element: <Register /> },
          { path: '/forgot-password', element: <ForgotPassword /> },
        ],
      },

      // ── Protected routes ───────────────────
      // (redirect to /login if not authenticated)
      {
        element: <ProtectedRoute />,
        children: [
          // Profile, orders, wishlist — added Week 10
          // Admin dashboard — added Week 9
        ],
      },

    ],
  },
])

export default router