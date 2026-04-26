import { useEffect, useState } from 'react';
import { useParams, useSearchParams, Link, useNavigate } from 'react-router-dom';
import {
  CheckCircle2, XCircle, Clock, Package,
  Truck, MapPin, ShoppingBag, RefreshCw,
} from 'lucide-react';

import { useOrder } from '../hooks/useOrders';
import orderAPI from '../api/orderAPI';
import { formatPrice } from '../utils/formatters';

/**
 * Landing page after IntaSend redirects the user back.
 *
 * IntaSend appends these query params to the redirect URL:
 *   ?checkout_id=<uuid>&invoice_id=<short-id>&order_tracking_id=<uuid>&status=<COMPLETE|FAILED>
 *
 * This page:
 *  1. Reads those params from the URL
 *  2. Calls verifyPayment() server-side — NEVER trusts the ?status= param alone
 *  3. Shows a success or failure state based on the server's response
 *  4. Fetches the full order for display via useOrder(orderNumber)
 *
 * Also works as a standalone order detail page when navigated to directly
 * (e.g. from the order history page) — in that case there are no URL params
 * and we just show the order detail without running verification.
 */

// ── Status badge ─────────────────────────────────────────────────────────────
const STATUS_STYLES = {
  pending:    'bg-yellow-500/10 text-yellow-400  border-yellow-500/30',
  paid:       'bg-blue-500/10   text-blue-400    border-blue-500/30',
  processing: 'bg-indigo-500/10 text-indigo-400  border-indigo-500/30',
  shipped:    'bg-violet-500/10 text-violet-400  border-violet-500/30',
  delivered:  'bg-green-500/10  text-green-400   border-green-500/30',
  cancelled:  'bg-red-500/10    text-red-400     border-red-500/30',
  refunded:   'bg-orange-500/10 text-orange-400  border-orange-500/30',
};

function StatusBadge({ status }) {
  const styles = STATUS_STYLES[status] || STATUS_STYLES.pending;
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${styles}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

// ── Skeleton loader ───────────────────────────────────────────────────────────
function ConfirmationSkeleton() {
  return (
    <div className="max-w-2xl mx-auto animate-pulse space-y-4">
      <div className="h-32 bg-slate-800 rounded-2xl" />
      <div className="h-64 bg-slate-800 rounded-2xl" />
      <div className="h-24 bg-slate-800 rounded-2xl" />
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function OrderConfirmation() {
  const { orderNumber }   = useParams();
  const [searchParams]    = useSearchParams();
  const navigate          = useNavigate();

  // URL params added by IntaSend on redirect back
  const checkoutId  = searchParams.get('checkout_id');
  const invoiceId   = searchParams.get('invoice_id');
  const urlStatus   = searchParams.get('status');   // NEVER trust this alone — always verify

  // Verification state
  const [verifying,      setVerifying]      = useState(false);
  const [verifyDone,     setVerifyDone]     = useState(false);
  const [verifySuccess,  setVerifySuccess]  = useState(false);
  const [verifyError,    setVerifyError]    = useState(null);

  // Fetch full order for display — enabled once verification is done (or if no params)
  const shouldFetchOrder = verifyDone || (!checkoutId && !invoiceId);
  const { data: order, isLoading: orderLoading, isError: orderError } = useOrder(
    shouldFetchOrder ? orderNumber : null
  );

  // ── Server-side verification on mount ────────────────────────────────────
  // Only runs when IntaSend redirect params are present in the URL.
  // We strip the params from the URL after verification so a page refresh
  // doesn't re-run verification unnecessarily.
  useEffect(() => {
    if (!checkoutId || !invoiceId) {
      // Direct navigation (e.g. from order history) — skip verification
      setVerifyDone(true);
      return;
    }

    const verify = async () => {
      setVerifying(true);
      try {
        const result = await orderAPI.verifyPayment({
          checkoutId,
          invoiceId,
        });

        if (result.status === 'COMPLETE') {
          setVerifySuccess(true);
        } else {
          setVerifyError(`Payment status: ${result.status}. ${result.detail || ''}`);
        }
      } catch (err) {
        // If the order was already verified (e.g. webhook beat us here),
        // the backend returns success — this is an actual error.
        const msg =
          err?.response?.data?.detail ||
          'Payment verification failed. Please contact support if you were charged.';
        setVerifyError(msg);
      } finally {
        setVerifyDone(true);
        setVerifying(false);

        // Clean up the URL — remove IntaSend params so a refresh doesn't re-verify
        navigate(`/order-confirmation/${orderNumber}`, { replace: true });
      }
    };

    verify();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Verifying state ───────────────────────────────────────────────────────
  if (verifying) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center gap-4">
        <div className="w-10 h-10 border-4 border-violet-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400 text-sm">Verifying your payment…</p>
      </div>
    );
  }

  // ── Payment failed state ──────────────────────────────────────────────────
  if (verifyDone && verifyError) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center px-4 text-center gap-4">
        <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center">
          <XCircle size={32} className="text-red-400" />
        </div>
        <h1 className="text-2xl font-bold text-white">Payment Not Completed</h1>
        <p className="text-slate-400 text-sm max-w-sm">{verifyError}</p>
        <p className="text-slate-500 text-xs max-w-sm">
          Your order <span className="text-violet-400 font-mono">{orderNumber}</span> has
          been saved. You can retry payment from your order history.
        </p>
        <div className="flex gap-3 mt-2">
          <Link
            to="/orders"
            className="px-5 py-2.5 border border-slate-700 hover:border-slate-500
                       text-slate-300 rounded-xl text-sm font-medium transition-colors"
          >
            My Orders
          </Link>
          <Link
            to="/products"
            className="px-5 py-2.5 bg-violet-600 hover:bg-violet-700
                       text-white rounded-xl text-sm font-medium transition-colors"
          >
            Continue Shopping
          </Link>
        </div>
      </div>
    );
  }

  // ── Loading order detail ──────────────────────────────────────────────────
  if (orderLoading) {
    return (
      <div className="min-h-screen bg-slate-950 py-10 px-4">
        <ConfirmationSkeleton />
      </div>
    );
  }

  // ── Order fetch error ─────────────────────────────────────────────────────
  if (orderError || !order) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center px-4 text-center gap-4">
        <p className="text-slate-400">Order not found.</p>
        <Link to="/orders" className="text-violet-400 hover:text-violet-300 text-sm">
          View all orders
        </Link>
      </div>
    );
  }

  // ── Success / Order detail ────────────────────────────────────────────────
  const isPaid = ['paid', 'processing', 'shipped', 'delivered'].includes(order.status);

  return (
    <div className="min-h-screen bg-slate-950 py-10 px-4">
      <div className="max-w-2xl mx-auto space-y-6">

        {/* ── Success / Status banner ─────────────────────────────────── */}
        <div className={`rounded-2xl p-6 text-center border ${
          isPaid
            ? 'bg-green-500/5 border-green-500/20'
            : 'bg-slate-800/60 border-slate-700'
        }`}>
          <div className="flex justify-center mb-4">
            {isPaid ? (
              <CheckCircle2 size={52} className="text-green-400" />
            ) : (
              <Clock size={52} className="text-yellow-400" />
            )}
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">
            {isPaid ? 'Order Confirmed!' : 'Order Placed'}
          </h1>
          <p className="text-slate-400 text-sm mb-4">
            {isPaid
              ? 'We received your payment and your order is being processed.'
              : 'Your order has been placed and is awaiting payment confirmation.'}
          </p>
          <div className="inline-flex items-center gap-2 bg-slate-900/60 px-4 py-2 rounded-xl">
            <span className="text-slate-400 text-sm">Order</span>
            <span className="text-violet-400 font-mono font-bold">{order.order_number}</span>
            <StatusBadge status={order.status} />
          </div>
        </div>

        {/* ── Order items ──────────────────────────────────────────────── */}
        <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-6">
          <h2 className="text-base font-semibold text-white mb-4">Items Ordered</h2>
          <ul className="space-y-4">
            {order.items.map((item, idx) => (
              <li key={idx} className="flex items-center gap-4">
                {item.image_url ? (
                  <img
                    src={item.image_url}
                    alt={item.product_name}
                    className="w-14 h-14 rounded-xl object-cover bg-slate-700 flex-shrink-0"
                  />
                ) : (
                  <div className="w-14 h-14 rounded-xl bg-slate-700 flex-shrink-0 flex items-center justify-center">
                    <Package size={20} className="text-slate-500" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{item.product_name}</p>
                  {(item.color || item.size) && (
                    <p className="text-xs text-slate-500 mt-0.5">
                      {[item.color, item.size].filter(Boolean).join(' / ')}
                    </p>
                  )}
                  <p className="text-xs text-slate-500 mt-0.5">Qty: {item.quantity}</p>
                </div>
                <div className="text-sm font-semibold text-slate-200 flex-shrink-0">
                  {formatPrice(item.subtotal)}
                </div>
              </li>
            ))}
          </ul>

          {/* Price breakdown */}
          <div className="border-t border-slate-700 mt-6 pt-4 space-y-2 text-sm">
            <div className="flex justify-between text-slate-400">
              <span>Subtotal</span>
              <span>{formatPrice(order.subtotal)}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Shipping ({order.shipping_method})</span>
              <span>{formatPrice(order.shipping_cost)}</span>
            </div>
            {order.discount > 0 && (
              <div className="flex justify-between text-green-400">
                <span>Discount</span>
                <span>−{formatPrice(order.discount)}</span>
              </div>
            )}
            <div className="flex justify-between text-base font-bold text-white pt-2 border-t border-slate-700">
              <span>Total</span>
              <span>{formatPrice(order.total)}</span>
            </div>
          </div>
        </div>

        {/* ── Shipping address ─────────────────────────────────────────── */}
        <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <MapPin size={16} className="text-violet-400" />
            <h2 className="text-base font-semibold text-white">Delivery Address</h2>
          </div>
          {order.shipping_address && (
            <address className="not-italic text-sm text-slate-400 space-y-1">
              <p className="text-slate-200 font-medium">{order.shipping_address.full_name}</p>
              <p>{order.shipping_address.phone}</p>
              <p>{order.shipping_address.street}</p>
              <p>{order.shipping_address.city}, {order.shipping_address.country}</p>
              {order.shipping_address.postal_code && (
                <p>{order.shipping_address.postal_code}</p>
              )}
            </address>
          )}
        </div>

        {/* ── What happens next ────────────────────────────────────────── */}
        <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-6">
          <h2 className="text-base font-semibold text-white mb-5">What happens next?</h2>
          <div className="flex flex-col sm:flex-row gap-4">
            {[
              {
                icon:  CheckCircle2,
                color: 'text-green-400',
                bg:    'bg-green-500/10',
                title: 'Order Confirmed',
                desc:  'Your order has been placed and payment received.',
              },
              {
                icon:  RefreshCw,
                color: 'text-blue-400',
                bg:    'bg-blue-500/10',
                title: 'Processing',
                desc:  'We are preparing your items for dispatch.',
              },
              {
                icon:  Truck,
                color: 'text-violet-400',
                bg:    'bg-violet-500/10',
                title: 'Shipped',
                desc:  'Your order is on its way. Tracking info will be added.',
              },
            ].map((step) => (
              <div key={step.title} className="flex-1 flex flex-col items-center text-center gap-2">
                <div className={`w-10 h-10 rounded-full ${step.bg} flex items-center justify-center`}>
                  <step.icon size={18} className={step.color} />
                </div>
                <p className="text-sm font-semibold text-white">{step.title}</p>
                <p className="text-xs text-slate-500">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* ── Actions ──────────────────────────────────────────────────── */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Link
            to="/orders"
            className="flex-1 py-3 border border-slate-700 hover:border-slate-500
                       text-slate-300 font-semibold rounded-xl
                       flex items-center justify-center gap-2
                       transition-colors text-sm"
          >
            <ShoppingBag size={15} />
            View Order History
          </Link>
          <Link
            to="/products"
            className="flex-1 py-3 bg-violet-600 hover:bg-violet-700
                       text-white font-semibold rounded-xl
                       flex items-center justify-center gap-2
                       transition-colors text-sm"
          >
            Continue Shopping
          </Link>
        </div>

      </div>
    </div>
  );
}