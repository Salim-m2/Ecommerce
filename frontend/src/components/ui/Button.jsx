// src/components/ui/Button.jsx

// ─────────────────────────────────────────────
// BUTTON COMPONENT
//
// Reusable button with variants and loading state.
// Usage:
//   <Button>Click me</Button>
//   <Button variant="outline" isLoading={true}>Save</Button>
//   <Button variant="danger" size="sm">Delete</Button>
// ─────────────────────────────────────────────

const variants = {
  primary: 'bg-violet-600 hover:bg-violet-700 text-white shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40',
  outline: 'border border-violet-500 text-violet-400 hover:bg-violet-500/10',
  danger:  'bg-red-500/10 border border-red-500/50 text-red-400 hover:bg-red-500/20',
  ghost:   'text-slate-400 hover:text-white hover:bg-white/5',
}

const sizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-5 py-2.5 text-sm',
  lg: 'px-7 py-3 text-base',
}

const Button = ({
  children,
  variant  = 'primary',
  size     = 'md',
  isLoading = false,
  disabled  = false,
  className = '',
  ...props
}) => {
  return (
    <button
      disabled={disabled || isLoading}
      className={`
        inline-flex items-center justify-center gap-2
        font-medium rounded-lg
        transition-all duration-200
        disabled:opacity-50 disabled:cursor-not-allowed
        ${variants[variant]}
        ${sizes[size]}
        ${className}
      `}
      {...props}
    >
      {isLoading && (
        <svg
          className="animate-spin h-4 w-4"
          viewBox="0 0 24 24"
          fill="none"
        >
          <circle
            className="opacity-25"
            cx="12" cy="12" r="10"
            stroke="currentColor" strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v8H4z"
          />
        </svg>
      )}
      {children}
    </button>
  )
}

export default Button