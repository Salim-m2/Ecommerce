// src/components/ui/Input.jsx

// ─────────────────────────────────────────────
// INPUT COMPONENT
//
// Reusable input with label, error display,
// and consistent dark theme styling.
// Designed to work with react-hook-form:
//   <Input
//     label="Email"
//     error={errors.email?.message}
//     {...register('email')}
//   />
// ─────────────────────────────────────────────
import { forwardRef } from 'react'

const Input = forwardRef(({
  label,
  error,
  className = '',
  ...props
}, ref) => {
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label className="text-sm font-medium text-slate-300">
          {label}
        </label>
      )}
      <input
        ref={ref}
        className={`
          w-full px-4 py-2.5
          bg-slate-800/50 border rounded-lg
          text-slate-100 placeholder-slate-500
          transition-all duration-200
          focus:outline-none focus:ring-2 focus:ring-violet-500/50
          ${error
            ? 'border-red-500/50 focus:ring-red-500/50'
            : 'border-slate-700 hover:border-slate-600'
          }
          ${className}
        `}
        {...props}
      />
      {error && (
        <p className="text-xs text-red-400 flex items-center gap-1">
          <span>⚠</span> {error}
        </p>
      )}
    </div>
  )
})

Input.displayName = 'Input'

export default Input