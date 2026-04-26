import { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom';
import { ShieldCheck, ExternalLink, AlertCircle, ArrowLeft } from 'lucide-react';

import orderAPI from '../api/orderAPI';
import { formatPrice } from '../utils/formatters';
import toast from 'react-hot-toast';

/**
 * Step 3 of checkout — Payment initiation.
 *
 * This page:
 *  1. Receives the created order (passed via router state from Step 2)
 *  2. Calls initializePayment(orderId) to get the IntaSend hosted payment URL
 *  3. Shows the order total and a "Pay Now" button
 *  4. On click → window.location.href = payment_url
 *     (IntaSend takes over from here; user pays on their hosted page)
 *
 * WHY a separate page instead of auto-redirecting:
 * Giving the user a moment to review their total before being sent to the
 * payment provider is better UX and gives them a chance to go back.
 */
export default function CheckoutPayment() {
  const { orderId }    = useParams();
  const location       = useLocation();
  const navigate       = useNavigate();

  // Order was passed via navigate(..., { state: { order } }) from Checkout.jsx
  const order = location.state?.order;

  const [paymentUrl,   setPaymentUrl]   = useState(null);
  const [checkoutId,   setCheckoutId]   = useState(null);
  const [isLoading,    setIsLoading]    = useState(true);
  const [isRedirecting, setIsRedirecting] = useState(false);
  const [error,        setError]        = useState(null);

  // ── Initialize payment on mount ──────────────────────────────────────────
  useEffect(() => {
    if (!orderId) {
      navigate('/checkout');
      return;
    }

    const initialize = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await orderAPI.initializePayment(orderId);
        setPaymentUrl(data.payment_url);
        setCheckoutId(data.checkout_id);
      } catch (err) {
        const msg =
          err?.response?.data?.detail ||
          'Could not initialize payment. Please try again.';
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    };

    initialize();
  }, [orderId, navigate]);

  // DEV ONLY — bypasses IntaSend and calls the test endpoint directly
  const handleDevConfirm = async () => {
    if (!order) return;
    setIsRedirecting(true);
    try {
      await orderAPI.devConfirmPayment(order.id);
      navigate(`/order-confirmation/${order.order_number}`);
    } catch (err) {
      toast.error('Dev confirm failed. Check console.');
      console.error(err);
      setIsRedirecting(false);
    }
  };

  // ── Handle Pay Now click ─────────────────────────────────────────────────
  const handlePayNow = () => {
    if (!paymentUrl) return;
    setIsRedirecting(true);
    // Redirect the whole page to IntaSend's hosted checkout.
    // IntaSend will redirect back to /order-confirmation/{orderNumber} when done.
    window.location.href = paymentUrl;
  };

  // ── Loading state ────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center gap-4">
        <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400 text-sm">Preparing your payment…</p>
      </div>
    );
  }

  // ── Error state ──────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center px-4 text-center gap-4">
        <div className="w-14 h-14 rounded-full bg-red-500/10 flex items-center justify-center">
          <AlertCircle size={28} className="text-red-400" />
        </div>
        <h2 className="text-xl font-bold text-white">Payment Initialization Failed</h2>
        <p className="text-slate-400 text-sm max-w-sm">{error}</p>
        <div className="flex gap-3 mt-2">
          <button
            onClick={() => navigate(-1)}
            className="px-5 py-2.5 border border-slate-700 hover:border-slate-500
                       text-slate-300 rounded-xl text-sm font-medium transition-colors"
          >
            Go Back
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-5 py-2.5 bg-violet-600 hover:bg-violet-700
                       text-white rounded-xl text-sm font-medium transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 py-10 px-4">
      <div className="max-w-md mx-auto">

        {/* Back link */}
        <Link
          to="/checkout"
          className="inline-flex items-center gap-1.5 text-slate-400 hover:text-slate-200
                     text-sm mb-8 transition-colors"
        >
          <ArrowLeft size={14} />
          Back to checkout
        </Link>

        {/* Card */}
        <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-6 md:p-8">

          {/* Header */}
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-violet-600/20 flex items-center justify-center">
              <ShieldCheck size={20} className="text-violet-400" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Secure Payment</h2>
              <p className="text-xs text-slate-500">Powered by IntaSend</p>
            </div>
          </div>

          {/* Order summary */}
          {order && (
            <div className="bg-slate-900/60 rounded-xl p-4 mb-6 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Order</span>
                <span className="text-violet-400 font-mono font-semibold">
                  {order.order_number}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Items</span>
                <span className="text-slate-300">{order.items?.length} item{order.items?.length !== 1 ? 's' : ''}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Shipping</span>
                <span className="text-slate-300">
                  {order.shipping_method === 'express' ? 'Express' : 'Standard'} ({formatPrice(order.shipping_cost)})
                </span>
              </div>
              <div className="border-t border-slate-700 pt-2 flex justify-between text-base font-semibold">
                <span className="text-white">Total to pay</span>
                <span className="text-violet-400">{formatPrice(order.total)}</span>
              </div>
            </div>
          )}

          {/* What to expect */}
          <div className="bg-slate-900/40 rounded-xl p-4 mb-6">
            <p className="text-xs text-slate-400 leading-relaxed">
              Clicking <strong className="text-slate-300">Pay Now</strong> will take you to
              IntaSend's secure payment page where you can pay via{' '}
              <strong className="text-slate-300">M-Pesa, card, or bank transfer</strong>.
              You will be returned here once payment is complete.
            </p>
          </div>

          {/* Pay Now button */}
          <button
            onClick={handlePayNow}
            disabled={!paymentUrl || isRedirecting}
            className="w-full py-4 bg-violet-600 hover:bg-violet-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold rounded-xl flex items-center justify-center gap-2 transition-colors text-sm">
            {isRedirecting ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Redirecting to IntaSend…
              </>
            ) : (
              <>
                <ExternalLink size={16} />
                Pay Now — {order ? formatPrice(order.total) : ''}
              </>
            )}
          </button>

          {/* DEV ONLY bypass button — remove before production */}
          {import.meta.env.DEV && order && (
            <button
              onClick={handleDevConfirm}
              className="w-full py-3 mt-2 border border-dashed border-yellow-600/50 hover:border-yellow-500 text-yellow-600 hover:text-yellow-500 rounded-xl text-xs font-medium transition-colors">
              ⚡ DEV: Skip payment and mark as paid
            </button>
          )}

          {/* Security note */}
          <p className="text-center text-xs text-slate-600 mt-4">
            🔒 Your payment is processed securely by IntaSend
          </p>
        </div>
      </div>
    </div>
  );
}