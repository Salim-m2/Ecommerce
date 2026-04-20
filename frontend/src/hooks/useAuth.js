// src/hooks/useAuth.js

import { useDispatch, useSelector } from 'react-redux'
import {
  loginUser,
  registerUser,
  logoutUser,
  clearError,
  selectCurrentUser,
  selectIsAuthenticated,
  selectAuthLoading,
  selectAuthError,
  selectIsInitialized,
} from '../store/authSlice'

// ─────────────────────────────────────────────
// useAuth HOOK
//
// Single interface for all auth operations.
// Components import this hook instead of
// touching Redux directly.
//
// Usage:
//   const { user, isAuthenticated, login } = useAuth()
// ─────────────────────────────────────────────
const useAuth = () => {
  const dispatch = useDispatch()

  const user            = useSelector(selectCurrentUser)
  const isAuthenticated = useSelector(selectIsAuthenticated)
  const isLoading       = useSelector(selectAuthLoading)
  const error           = useSelector(selectAuthError)
  const isInitialized   = useSelector(selectIsInitialized)

  const login = (credentials) => dispatch(loginUser(credentials))
  const register = (data)     => dispatch(registerUser(data))
  const logout = ()           => dispatch(logoutUser())
  const clear = ()            => dispatch(clearError())

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    isInitialized,
    login,
    register,
    logout,
    clearError: clear,
  }
}

export default useAuth