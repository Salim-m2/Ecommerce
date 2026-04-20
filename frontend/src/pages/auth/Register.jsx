// src/pages/auth/Register.jsx

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
const registerSchema = z.object({
  first_name: z.string()
    .min(1, 'First name is required.'),
  last_name: z.string()
    .min(1, 'Last name is required.'),
  email: z.string()
    .email('Please enter a valid email address.'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters.'),
  confirm_password: z.string()
    .min(1, 'Please confirm your password.'),
}).refine(
  (data) => data.password === data.confirm_password,
  {
    message: 'Passwords do not match.',
    path:    ['confirm_password'],
  }
)

// ─────────────────────────────────────────────
// REGISTER PAGE
// ─────────────────────────────────────────────
const Register = () => {
  const navigate                          = useNavigate()
  const { register: registerUser, isLoading, error, clearError } = useAuth()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({ resolver: zodResolver(registerSchema) })

  // Clear errors when component unmounts
  useEffect(() => {
    return () => clearError()
  }, [])

  const onSubmit = async (data) => {
    const result = await registerUser(data)
    if (result.meta.requestStatus === 'fulfilled') {
      toast.success('Account created! Please sign in.')
      navigate('/login')
    }
  }

  // Format API errors — can be object or string
  const getApiError = () => {
    if (!error) return null
    if (typeof error === 'string') return error
    if (typeof error === 'object') {
      return Object.values(error).flat().join(' ')
    }
    return 'Registration failed. Please try again.'
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4 py-12">

      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-teal-600/10 rounded-full blur-3xl" />
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
          <p className="text-slate-400 mt-2 text-sm">Create your account</p>
        </div>

        {/* Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">

          {/* API Error */}
          {error && (
            <div className="mb-6 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
              <p className="text-red-400 text-sm">{getApiError()}</p>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">

            {/* Name row */}
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="First name"
                placeholder="Jane"
                error={errors.first_name?.message}
                {...register('first_name')}
              />
              <Input
                label="Last name"
                placeholder="Doe"
                error={errors.last_name?.message}
                {...register('last_name')}
              />
            </div>

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
              placeholder="Min. 8 characters"
              error={errors.password?.message}
              {...register('password')}
            />

            <Input
              label="Confirm password"
              type="password"
              placeholder="••••••••"
              error={errors.confirm_password?.message}
              {...register('confirm_password')}
            />

            <Button
              type="submit"
              isLoading={isLoading}
              className="w-full mt-1"
            >
              Create Account
            </Button>

          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-3">
            <div className="flex-1 h-px bg-slate-800" />
            <span className="text-xs text-slate-600">OR</span>
            <div className="flex-1 h-px bg-slate-800" />
          </div>

          {/* Login link */}
          <p className="text-center text-sm text-slate-500">
            Already have an account?{' '}
            <Link
              to="/login"
              className="text-violet-400 hover:text-violet-300 font-medium transition-colors"
            >
              Sign in
            </Link>
          </p>

        </div>

        {/* Footer note */}
        <p className="text-center text-xs text-slate-600 mt-6">
          By creating an account you agree to our Terms of Service
        </p>

      </div>
    </div>
  )
}

export default Register