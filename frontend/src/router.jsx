import { createBrowserRouter, Outlet, Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { selectIsAuthenticated, selectIsInitialized } from './store/authSlice'

import Navbar      from './components/layout/Navbar'
import Footer      from './components/layout/Footer'
import CartDrawer  from './components/cart/CartDrawer'
import Spinner     from './components/ui/Spinner'

import Home          from './pages/Home'
import Login         from './pages/auth/Login'
import Register      from './pages/auth/Register'
import ForgotPassword from './pages/auth/ForgotPassword'
import ProductList   from './pages/ProductList'
import ProductDetail from './pages/ProductDetail'
import Cart from './pages/Cart'
import Checkout from './pages/Checkout';
import CheckoutPayment  from './pages/CheckoutPayment';
import OrderConfirmation from './pages/OrderConfirmation';
import Orders from './pages/user/Orders';

const RootLayout = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />
      <CartDrawer />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}

const ProtectedRoute = () => {
  const isAuthenticated = useSelector(selectIsAuthenticated)
  const isInitialized   = useSelector(selectIsInitialized)

  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

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

const NotFound = () => (
  <div className="min-h-[60vh] flex flex-col items-center justify-center text-center px-4">
    <p className="text-8xl font-extrabold text-violet-500/20 mb-4">404</p>
    <h1 className="text-2xl font-bold text-white mb-2">Page not found</h1>
    <p className="text-slate-400 text-sm mb-8">
      The page you're looking for doesn't exist or hasn't been built yet.
    </p>
    
     <a href="/"
      className="px-5 py-2.5 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm font-medium transition-colors"
    >
      Back to home
    </a>
  </div>
)

const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      { path: '/',               element: <Home /> },
      { path: '/products',       element: <ProductList /> },
      { path: '/products/:slug', element: <ProductDetail /> },
      { path: '/cart',           element: <Cart /> },
      { path: '/order-confirmation/:orderNumber', element: <OrderConfirmation /> },
      {
        element: <GuestRoute />,
        children: [
          { path: '/login',           element: <Login /> },
          { path: '/register',        element: <Register /> },
          { path: '/forgot-password', element: <ForgotPassword /> },
        ],
      },
      {
        element: <ProtectedRoute />,
        children: [
          { path: '/profile', element: <div className="p-8 text-white">Profile — Week 10</div> },
          { path: '/checkout', element: <Checkout /> },
          { path: '/checkout/payment/:orderId', element: <CheckoutPayment /> },
          { path: '/orders', element: <Orders /> },
        ],
      },
      { path: '*', element: <NotFound /> },
    ],
  },
])

export default router