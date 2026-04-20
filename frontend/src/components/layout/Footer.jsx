// src/components/layout/Footer.jsx

import { Link } from 'react-router-dom'

const Footer = () => {
  return (
    <footer className="bg-slate-950 border-t border-slate-800 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">

          {/* Brand */}
          <Link to="/" className="flex items-center gap-2 text-lg font-bold">
            <span>⚡</span>
            <span className="bg-gradient-to-r from-violet-400 to-teal-400 bg-clip-text text-transparent">
              ShopZetu
            </span>
          </Link>

          {/* Links */}
          <div className="flex items-center gap-6 text-sm text-slate-500">
            <Link to="/products" className="hover:text-slate-300 transition-colors">
              Products
            </Link>
            <Link to="/cart" className="hover:text-slate-300 transition-colors">
              Cart
            </Link>
            <Link to="/login" className="hover:text-slate-300 transition-colors">
              Sign in
            </Link>
          </div>

          {/* Copyright */}
          <p className="text-xs text-slate-600">
            © {new Date().getFullYear()} ShopZetu. All rights reserved.
          </p>

        </div>
      </div>
    </footer>
  )
}

export default Footer