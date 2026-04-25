import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShoppingBag, ChevronLeft, Tag } from 'lucide-react';
import toast from 'react-hot-toast';

import useCart from '../hooks/useCart';
import CartItem from '../components/cart/CartItem';
import CartSummary from '../components/cart/CartSummary';
import { formatPrice } from '../utils/formatters';
import cartAPI from '../api/cartAPI';

// ── Skeleton row ───────────────────────────────────────────────────────────

const CartItemSkeleton = () => (
  <div className="flex gap-3 py-4 border-b border-slate-700/50 animate-pulse">
    <div className="w-16 h-16 bg-slate-700 rounded-lg flex-shrink-0" />
    <div className="flex-1 space-y-2">
      <div className="h-4 bg-slate-700 rounded w-3/4" />
      <div className="h-3 bg-slate-700 rounded w-1/2" />
      <div className="h-3 bg-slate-700 rounded w-1/4" />
    </div>
  </div>
);

// ── Coupon input ───────────────────────────────────────────────────────────

const CouponInput = () => {
  const [code, setCode]       = useState('');
  const [loading, setLoading] = useState(false);

  const handleApply = async () => {
    if (!code.trim()) return;
    setLoading(true);
    try {
      const data = await cartAPI.applyCoupon(code.trim());
      toast(data.detail || 'Coupon applied.', { icon: '🏷️' });
    } catch {
      toast.error('Invalid or expired coupon code.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex gap-2 mt-4">
      <div className="relative flex-1">
        <Tag
          size={14}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
        />
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === 'Enter' && handleApply()}
          placeholder="Coupon code"
          className="w-full pl-8 pr-3 py-2.5 bg-slate-800 border border-slate-600
                     rounded-xl text-sm text-white placeholder-slate-500
                     focus:outline-none focus:border-violet-500 transition-colors"
        />
      </div>
      <button
        onClick={handleApply}
        disabled={loading || !code.trim()}
        className="px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-white text-sm
                   font-medium rounded-xl transition-colors disabled:opacity-50
                   disabled:cursor-not-allowed"
      >
        {loading ? 'Applying…' : 'Apply'}
      </button>
    </div>
  );
};

// ── Main Cart page ─────────────────────────────────────────────────────────

const Cart = () => {
  const navigate = useNavigate();
  const {
    cart,
    items,
    itemCount,
    subtotal,
    isLoading,
    updateItem,
    removeItem,
  } = useCart();

  const handleUpdate = async (itemIndex, quantity) => {
    const result = await updateItem(itemIndex, quantity);
    if (!result.success) {
      toast.error(result.error || 'Could not update quantity.');
    }
  };

  const handleRemove = async (itemIndex) => {
    const result = await removeItem(itemIndex);
    if (!result.success) {
      toast.error(result.error || 'Could not remove item.');
    }
  };

  const handleClearCart = async () => {
    // Remove all items one by one from the end to avoid index shifting
    for (let i = items.length - 1; i >= 0; i--) {
      await removeItem(i);
    }
    toast.success('Cart cleared.');
  };

  const handleCheckout = () => {
    toast('Checkout coming in Week 6!', { icon: '🛒' });
  };

  // ── Loading state ────────────────────────────────────────────────────

  if (isLoading && !cart) {
    return (
      <div className="min-h-screen bg-slate-950 px-4 py-8">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-2xl font-bold text-white mb-8">Shopping Cart</h1>
          <div className="lg:grid lg:grid-cols-3 lg:gap-8">
            <div className="lg:col-span-2 space-y-0">
              {[1, 2, 3].map((n) => <CartItemSkeleton key={n} />)}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── Empty state ──────────────────────────────────────────────────────

  if (!isLoading && items.length === 0) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center
                      justify-center px-4 text-center">
        <ShoppingBag size={64} className="text-slate-700 mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">
          Your cart is empty
        </h2>
        <p className="text-slate-400 mb-8 max-w-sm">
          Looks like you haven't added anything yet.
          Browse our products and find something you love.
        </p>
        <Link
          to="/products"
          className="px-6 py-3 bg-violet-600 hover:bg-violet-700 text-white
                     font-semibold rounded-xl transition-colors"
        >
          Start Shopping
        </Link>
      </div>
    );
  }

  // ── Cart with items ──────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-8">
      <div className="max-w-5xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link
              to="/products"
              className="flex items-center gap-1.5 text-slate-400
                         hover:text-white transition-colors text-sm"
            >
              <ChevronLeft size={16} />
              Continue Shopping
            </Link>
            <h1 className="text-2xl font-bold text-white">
              Shopping Cart
              <span className="text-slate-400 font-normal text-lg ml-2">
                ({itemCount} item{itemCount !== 1 ? 's' : ''})
              </span>
            </h1>
          </div>

          {/* Clear cart */}
          {items.length > 0 && (
            <button
              onClick={handleClearCart}
              disabled={isLoading}
              className="text-sm text-slate-500 hover:text-red-400
                         transition-colors disabled:opacity-50"
            >
              Clear cart
            </button>
          )}
        </div>

        {/* Two-column layout on desktop */}
        <div className="lg:grid lg:grid-cols-3 lg:gap-8 items-start">

          {/* Left: Cart items (takes 2/3 width) */}
          <div className="lg:col-span-2">
            <div className="bg-slate-900 rounded-2xl border border-slate-700/50
                            px-5 divide-y divide-slate-700/30">
              {items.map((item, index) => (
                <CartItem
                  key={`${item.product_id}-${item.variant_id}`}
                  item={item}
                  itemIndex={index}
                  onUpdate={handleUpdate}
                  onRemove={handleRemove}
                  isUpdating={isLoading}
                />
              ))}
            </div>
          </div>

          {/* Right: Order summary (takes 1/3 width) */}
          <div className="mt-6 lg:mt-0">
            <div className="bg-slate-900 rounded-2xl border border-slate-700/50 p-5">
              <h2 className="text-white font-bold text-lg mb-4">
                Order Summary
              </h2>

              <CartSummary
                subtotal={subtotal}
                itemCount={itemCount}
                onCheckout={handleCheckout}
              />

              {/* Coupon input */}
              <div className="border-t border-slate-700/50 pt-4 mt-2">
                <p className="text-sm text-slate-400 font-medium mb-1">
                  Have a coupon?
                </p>
                <CouponInput />
              </div>
            </div>

            {/* Order details summary */}
            <div className="mt-4 bg-slate-900 rounded-2xl border border-slate-700/50 p-5">
              <h3 className="text-white font-semibold text-sm mb-3">
                Price Breakdown
              </h3>
              <div className="space-y-2">
                {items.map((item, index) => (
                  <div
                    key={`${item.product_id}-${item.variant_id}`}
                    className="flex justify-between text-xs text-slate-400"
                  >
                    <span className="truncate pr-2 max-w-[180px]">
                      {item.product_name}
                      {item.size ? ` (${item.size})` : ''}
                      {' '}× {item.quantity}
                    </span>
                    <span className="flex-shrink-0 text-slate-300">
                      {formatPrice(item.price_at_add * item.quantity)}
                    </span>
                  </div>
                ))}
                <div className="border-t border-slate-700/50 pt-2 mt-2
                                flex justify-between text-sm font-semibold">
                  <span className="text-slate-300">Total</span>
                  <span className="text-white">{formatPrice(subtotal)}</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Cart;