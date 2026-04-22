// src/components/layout/Navbar.jsx

import { Link, useNavigate } from 'react-router-dom'
import { Search, ShoppingCart, User, LogOut, Menu, X, ShoppingBag} from 'lucide-react';
import { useState } from 'react'
import toast from 'react-hot-toast'
import useAuth from '../../hooks/useAuth'
import { useSelector } from 'react-redux'
import { selectCartCount } from '../../store/cartSlice'
import { useDispatch } from 'react-redux';
import { logoutUser } from '../../store/authSlice';

// ─────────────────────────────────────────────
// NAVBAR COMPONENT
//
// Shows different content based on auth state:
// - Unauthenticated: Login + Register links
// - Authenticated: User name + Logout button
// ─────────────────────────────────────────────
const Navbar = () => {
  const navigate            = useNavigate()
  const { user, isAuthenticated, logout } = useAuth()
  const cartCount           = useSelector(selectCartCount)
  const [menuOpen, setMenuOpen] = useState(false)
  const [query, setQuery] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/products?search=${encodeURIComponent(query.trim())}`);
      setQuery('');
    }
  };

  const handleLogout = async () => {
    await logout()
    toast.success('Logged out successfully.')
    navigate('/login')
  }


  return (
    <nav className="sticky top-0 z-50 bg-slate-950/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">

          {/* ── Logo ── */}
          <Link
            to="/"
            className="flex items-center gap-2 text-xl font-bold"
          >
            <span>⚡</span>
            <span className="bg-gradient-to-r from-violet-400 to-teal-400 bg-clip-text text-transparent">
              ShopZetu
            </span>
          </Link>
          {/* Search form */}
          {/* <form onSubmit={handleSearch} className="flex-1 max-w-md">
            <div className="relative">
              <Search
                size={15}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"
              />
              <input
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Search products..."
                className="w-full pl-8 pr-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-gray-50"
              />
            </div>
          </form> */}
          {/* ── Desktop Nav ── */}
          <div className="hidden md:flex items-center gap-6">

            <Link
              to="/products"
              className="text-sm text-slate-400 hover:text-white transition-colors"
            >
              Products
            </Link>

            {/* Cart icon */}
            <Link
              to="/cart"
              className="relative text-slate-400 hover:text-white transition-colors"
            >
              <ShoppingBag size={20} />
              {cartCount > 0 && (
                <span className="absolute -top-2 -right-2 bg-violet-600 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center font-bold">
                  {cartCount > 9 ? '9+' : cartCount}
                </span>
              )}
            </Link>

            {/* Auth section */}
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <Link
                  to="/profile"
                  className="flex items-center gap-2 text-sm text-slate-300 hover:text-white transition-colors"
                >
                  <div className="h-7 w-7 rounded-full bg-violet-600/20 border border-violet-500/30 flex items-center justify-center">
                    <User size={14} className="text-violet-400" />
                  </div>
                  <span>{user?.first_name}</span>
                </Link>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-red-400 transition-colors"
                >
                  <LogOut size={16} />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  to="/login"
                  className="text-sm text-slate-400 hover:text-white transition-colors"
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="text-sm bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg transition-colors font-medium"
                >
                  Get started
                </Link>
              </div>
            )}
          </div>

          {/* ── Mobile menu button ── */}
          <button
            className="md:hidden text-slate-400 hover:text-white transition-colors"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>

        </div>
      </div>

      {/* ── Mobile Menu ── */}
      {menuOpen && (
        <div className="md:hidden border-t border-slate-800 bg-slate-950 px-4 py-4 flex flex-col gap-4">

          <Link
            to="/products"
            className="text-sm text-slate-400 hover:text-white transition-colors"
            onClick={() => setMenuOpen(false)}
          >
            Products
          </Link>

          <Link
            to="/cart"
            className="text-sm text-slate-400 hover:text-white transition-colors flex items-center gap-2"
            onClick={() => setMenuOpen(false)}
          >
            <ShoppingBag size={16} />
            Cart {cartCount > 0 && `(${cartCount})`}
          </Link>

          {isAuthenticated ? (
            <>
              <Link
                to="/profile"
                className="text-sm text-slate-300 hover:text-white transition-colors"
                onClick={() => setMenuOpen(false)}
              >
                {user?.first_name} {user?.last_name}
              </Link>
              <button
                onClick={() => { handleLogout(); setMenuOpen(false) }}
                className="text-sm text-red-400 hover:text-red-300 transition-colors text-left"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm text-slate-400 hover:text-white transition-colors"
                onClick={() => setMenuOpen(false)}
              >
                Sign in
              </Link>
              <Link
                to="/register"
                className="text-sm bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg transition-colors font-medium text-center"
                onClick={() => setMenuOpen(false)}
              >
                Get started
              </Link>
            </>
          )}

        </div>
      )}
    </nav>
  )
}

export default Navbar