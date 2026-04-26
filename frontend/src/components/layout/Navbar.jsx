import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import {
  ShoppingCart, Search, ChevronDown,
  User, Package, LogOut, Menu, X,
} from 'lucide-react';

import useAuth              from '../../hooks/useAuth';
import { selectCartItemCount }  from '../../store/cartSlice';
import { toggleCartDrawer }     from '../../store/cartSlice';
import { logoutUser }           from '../../store/authSlice';
import { useSelector }          from 'react-redux';

export default function Navbar() {
  const dispatch    = useDispatch();
  const navigate    = useNavigate();
  const { user, isAuthenticated } = useAuth();

  const itemCount   = useSelector(selectCartItemCount);

  const [searchTerm,   setSearchTerm]   = useState('');
  const [mobileOpen,   setMobileOpen]   = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // ── Search ────────────────────────────────────────────────────────────────
  const handleSearch = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      navigate(`/products?search=${encodeURIComponent(searchTerm.trim())}`);
      setSearchTerm('');
      setMobileOpen(false);
    }
  };

  // ── Logout ────────────────────────────────────────────────────────────────
  const handleLogout = () => {
    dispatch(logoutUser());
    setUserMenuOpen(false);
    setMobileOpen(false);
    navigate('/');
  };

  return (
    <nav className="sticky top-0 z-40 bg-slate-900/95 backdrop-blur-sm
                    border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">

          {/* ── Logo ──────────────────────────────────────────────────── */}
          <Link
            to="/"
            className="text-lg font-bold text-white hover:text-violet-400
                       transition-colors flex-shrink-0"
          >
            MyStore
          </Link>

          {/* ── Search bar (desktop) ──────────────────────────────────── */}
          <form
            onSubmit={handleSearch}
            className="hidden md:flex flex-1 max-w-md"
          >
            <div className="relative w-full">
              <Search
                size={15}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
              />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search products…"
                className="w-full bg-slate-800 border border-slate-700
                           rounded-xl pl-9 pr-4 py-2 text-sm text-white
                           placeholder-slate-500
                           focus:outline-none focus:border-violet-500
                           focus:ring-1 focus:ring-violet-500 transition-colors"
              />
            </div>
          </form>

          {/* ── Right side ────────────────────────────────────────────── */}
          <div className="flex items-center gap-2">

            {/* Cart icon */}
            <button
              onClick={() => dispatch(toggleCartDrawer())}
              className="relative p-2 text-slate-400 hover:text-white transition-colors"
              aria-label="Open cart"
            >
              <ShoppingCart size={20} />
              {itemCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5
                                 bg-violet-600 text-white text-xs
                                 w-4 h-4 rounded-full
                                 flex items-center justify-center font-bold">
                  {itemCount > 9 ? '9+' : itemCount}
                </span>
              )}
            </button>

            {/* ── Authenticated user dropdown ──────────────────────── */}
            {isAuthenticated ? (
              <div className="relative hidden md:block">
                <button
                  onClick={() => setUserMenuOpen(prev => !prev)}
                  onBlur={() => setTimeout(() => setUserMenuOpen(false), 150)}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-xl
                             text-sm text-slate-300 hover:text-white
                             hover:bg-slate-800 transition-colors"
                >
                  <User size={15} />
                  <span className="font-medium">{user?.first_name}</span>
                  <ChevronDown
                    size={13}
                    className={`transition-transform duration-200 ${userMenuOpen ? 'rotate-180' : ''}`}
                  />
                </button>

                {/* Dropdown panel */}
                {userMenuOpen && (
                  <div className="absolute right-0 top-full mt-1 w-44
                                  bg-slate-800 border border-slate-700
                                  rounded-xl shadow-xl z-50 overflow-hidden">
                    <div className="px-4 py-3 border-b border-slate-700">
                      <p className="text-xs text-slate-500">Signed in as</p>
                      <p className="text-sm font-medium text-white truncate">
                        {user?.email}
                      </p>
                    </div>

                    <Link
                      to="/orders"
                      onClick={() => setUserMenuOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-2.5
                                 text-sm text-slate-300 hover:text-white
                                 hover:bg-slate-700 transition-colors"
                    >
                      <Package size={14} />
                      My Orders
                    </Link>

                    <Link
                      to="/profile"
                      onClick={() => setUserMenuOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-2.5
                                 text-sm text-slate-300 hover:text-white
                                 hover:bg-slate-700 transition-colors"
                    >
                      <User size={14} />
                      Profile
                    </Link>

                    <div className="border-t border-slate-700">
                      <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-2.5 px-4 py-2.5
                                   text-sm text-red-400 hover:text-red-300
                                   hover:bg-slate-700 transition-colors"
                      >
                        <LogOut size={14} />
                        Logout
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              /* Guest links */
              <div className="hidden md:flex items-center gap-2">
                <Link
                  to="/login"
                  className="px-3 py-2 text-sm text-slate-400
                             hover:text-white transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 bg-violet-600 hover:bg-violet-700
                             text-white text-sm font-semibold rounded-xl
                             transition-colors"
                >
                  Register
                </Link>
              </div>
            )}

            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileOpen(prev => !prev)}
              className="md:hidden p-2 text-slate-400 hover:text-white transition-colors"
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </div>

      {/* ── Mobile menu ─────────────────────────────────────────────────── */}
      {mobileOpen && (
        <div className="md:hidden border-t border-slate-800 bg-slate-900 px-4 py-4 space-y-3">

          {/* Mobile search */}
          <form onSubmit={handleSearch}>
            <div className="relative">
              <Search
                size={15}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
              />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search products…"
                className="w-full bg-slate-800 border border-slate-700
                           rounded-xl pl-9 pr-4 py-2.5 text-sm text-white
                           placeholder-slate-500
                           focus:outline-none focus:border-violet-500 transition-colors"
              />
            </div>
          </form>

          {isAuthenticated ? (
            <>
              <div className="px-1 py-2 border-t border-slate-800">
                <p className="text-xs text-slate-500 mb-1">Signed in as</p>
                <p className="text-sm font-medium text-white">{user?.email}</p>
              </div>
              <Link
                to="/orders"
                onClick={() => setMobileOpen(false)}
                className="flex items-center gap-2.5 px-1 py-2.5
                           text-sm text-slate-300 hover:text-white transition-colors"
              >
                <Package size={15} />
                My Orders
              </Link>
              <Link
                to="/profile"
                onClick={() => setMobileOpen(false)}
                className="flex items-center gap-2.5 px-1 py-2.5
                           text-sm text-slate-300 hover:text-white transition-colors"
              >
                <User size={15} />
                Profile
              </Link>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2.5 px-1 py-2.5
                           text-sm text-red-400 hover:text-red-300 transition-colors"
              >
                <LogOut size={15} />
                Logout
              </button>
            </>
          ) : (
            <div className="flex flex-col gap-2 pt-2 border-t border-slate-800">
              <Link
                to="/login"
                onClick={() => setMobileOpen(false)}
                className="py-2.5 text-center text-sm text-slate-300
                           hover:text-white transition-colors"
              >
                Login
              </Link>
              <Link
                to="/register"
                onClick={() => setMobileOpen(false)}
                className="py-2.5 bg-violet-600 hover:bg-violet-700
                           text-white text-sm font-semibold rounded-xl
                           text-center transition-colors"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      )}
    </nav>
  );
}