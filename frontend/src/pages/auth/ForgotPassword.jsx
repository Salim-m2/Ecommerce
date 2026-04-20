// src/pages/auth/ForgotPassword.jsx

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { requestPasswordReset } from '../../api/authAPI'
import Button from '../../components/ui/Button'
import Input  from '../../components/ui/Input'

const schema = z.object({
  email: z.string().email('Please enter a valid email address.'),
})

const ForgotPassword = () => {
  const [submitted, setSubmitted] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({ resolver: zodResolver(schema) })

  const onSubmit = async (data) => {
    setIsLoading(true)
    try {
      await requestPasswordReset(data.email)
      setSubmitted(true)
    } catch {
      toast.error('Something went wrong. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4">

      <div className="w-full max-w-md">

        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 text-2xl font-bold">
            <span>⚡</span>
            <span className="bg-gradient-to-r from-violet-400 to-teal-400 bg-clip-text text-transparent">
              ShopZetu
            </span>
          </Link>
          <p className="text-slate-400 mt-2 text-sm">Reset your password</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">

          {submitted ? (
            <div className="text-center">
              <div className="text-4xl mb-4">📬</div>
              <h2 className="text-white font-semibold text-lg mb-2">
                Check your email
              </h2>
              <p className="text-slate-400 text-sm mb-6">
                If that email exists in our system, a reset link has been sent.
              </p>
              <Link
                to="/login"
                className="text-violet-400 hover:text-violet-300 text-sm transition-colors"
              >
                Back to sign in
              </Link>
            </div>
          ) : (
            <>
              <p className="text-slate-400 text-sm mb-6">
                Enter your email and we'll send you a reset link.
              </p>

              <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
                <Input
                  label="Email address"
                  type="email"
                  placeholder="jane@example.com"
                  error={errors.email?.message}
                  {...register('email')}
                />
                <Button type="submit" isLoading={isLoading} className="w-full">
                  Send Reset Link
                </Button>
              </form>

              <p className="text-center text-sm text-slate-500 mt-6">
                Remember your password?{' '}
                <Link
                  to="/login"
                  className="text-violet-400 hover:text-violet-300 transition-colors"
                >
                  Sign in
                </Link>
              </p>
            </>
          )}

        </div>
      </div>
    </div>
  )
}

export default ForgotPassword