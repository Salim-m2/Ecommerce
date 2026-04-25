// src/pages/auth/Login.jsx

import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import useAuth from '../../hooks/useAuth'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'

// ─────────────────────────────────────────────
// VALIDATION SCHEMA
// ─────────────────────────────────────────────
const loginSchema = z.object({
  email:    z.string().email('Please enter a valid email address.'),
  password: z.string().min(1, 'Password is required.'),
})

// ─────────────────────────────────────────────
// LOGIN PAGE
// ─────────────────────────────────────────────
const Login = () => {
  const navigate          = useNavigate()
  const { login, isLoading, error, isAuthenticated, clearError } = useAuth()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({ resolver: zodResolver(loginSchema) })

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) navigate('/')
  }, [isAuthenticated, navigate])

  // Clear errors when component unmounts
  useEffect(() => {
    return () => clearError()
  }, [])

  const onSubmit = async (data) => {
    const result = await login(data)
    if (result.meta.requestStatus === 'fulfilled') {
      toast.success('Welcome back!')
      navigate('/')
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4">

      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative">

        {/* Logo / Brand */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 text-2xl font-bold">
            <span className="text-2xl">⚡</span>
            <span className="bg-gradient-to-r from-violet-400 to-teal-400 bg-clip-text text-transparent">
              ShopZetu
            </span>
          </Link>
          <p className="text-slate-400 mt-2 text-sm">Sign in to your account</p>
        </div>

        {/* Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">

          {/* API Error */}
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl">
              <p className="text-red-400 text-sm text-center">
                {typeof error === 'string'
                  ? error
                  : error?.detail
                  ?? error?.non_field_errors?.[0]
                  ?? 'Login failed. Please check your credentials.'}
              </p>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">

            <Input
              label="Email address"
              type="email"
              placeholder="jane@example.com"
              error={errors.email?.message}
              {...register('email')}
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              error={errors.password?.message}
              {...register('password')}
            />

            {/* Forgot password link */}
            <div className="flex justify-end -mt-2">
              <Link
                to="/forgot-password"
                className="text-xs text-violet-400 hover:text-violet-300 transition-colors"
              >
                Forgot your password?
              </Link>
            </div>

            <Button
              type="submit"
              isLoading={isLoading}
              className="w-full mt-1"
            >
              Sign In
            </Button>

          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-3">
            <div className="flex-1 h-px bg-slate-800" />
            <span className="text-xs text-slate-600">OR</span>
            <div className="flex-1 h-px bg-slate-800" />
          </div>

          {/* Register link */}
          <p className="text-center text-sm text-slate-500">
            Don't have an account?{' '}
            <Link
              to="/register"
              className="text-violet-400 hover:text-violet-300 font-medium transition-colors"
            >
              Create one
            </Link>
          </p>

        </div>

        {/* Footer note */}
        <p className="text-center text-xs text-slate-600 mt-6">
          By signing in you agree to our Terms of Service
        </p>

      </div>
    </div>
  )
}

export default Login