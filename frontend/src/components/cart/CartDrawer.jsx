import { useEffect } from 'react';
import { X, ShoppingCart } from 'lucide-react';
import { useDispatch } from 'react-redux';
import toast from 'react-hot-toast';

import useCart from '../../hooks/useCart';
import CartItem from './CartItem';
import CartSummary from './CartSummary';

/**
 * Slide-in cart drawer from the right side of the screen.
 * Rendered once in the Layout so it persists across all page navigations.
 *
 * - Semi-transparent overlay closes the drawer when clicked.
 * - Transforms translateX(100%) → translateX(0) with a CSS transition.
 * - Empty state, loading skeletons, and live item list are all handled here.
 */
const CartDrawer = () => {
  const {
    items,
    itemCount,
    subtotal,
    isOpen,
    isLoading,
    updateItem,
    removeItem,
    closeDrawer,
  } = useCart();

  // Prevent body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

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

  const handleCheckout = () => {
    toast('Checkout coming in Week 6!', { icon: '🛒' });
  };

  return (
    <>
      {/* ── Overlay ───────────────────────────────────────────────── */}
      <div
        className={`fixed inset-0 bg-black/60 backdrop-blur-sm z-40
                    transition-opacity duration-300
                    ${isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
        onClick={closeDrawer}
        aria-hidden="true"
      />

      {/* ── Drawer panel ──────────────────────────────────────────── */}
      <div
        className={`fixed top-0 right-0 h-full w-full max-w-md bg-slate-900
                    border-l border-slate-700/50 shadow-2xl z-50
                    flex flex-col transition-transform duration-300 ease-in-out
                    ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}
        role="dialog"
        aria-label="Shopping cart"
      >
        {/* ── Header ──────────────────────────────────────────────── */}
        <div className="flex items-center justify-between px-5 py-4
                        border-b border-slate-700/50 flex-shrink-0">
          <div className="flex items-center gap-2">
            <ShoppingCart size={20} className="text-violet-400" />
            <h2 className="text-white font-bold text-lg">Your Cart</h2>
            {itemCount > 0 && (
              <span className="bg-violet-600 text-white text-xs font-bold
                               px-2 py-0.5 rounded-full">
                {itemCount}
              </span>
            )}
          </div>

          <button
            onClick={closeDrawer}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700
                       rounded-lg transition-colors"
            aria-label="Close cart"
          >
            <X size={18} />
          </button>
        </div>

        {/* ── Body ────────────────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto px-5">
          {/* Loading skeletons */}
          {isLoading && items.length === 0 && (
            <div className="space-y-4 pt-4">
              {[1, 2, 3].map((n) => (
                <div key={n} className="flex gap-3 py-4 border-b border-slate-700/50">
                  <div className="w-16 h-16 bg-slate-700 rounded-lg animate-pulse flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-slate-700 rounded animate-pulse w-3/4" />
                    <div className="h-3 bg-slate-700 rounded animate-pulse w-1/2" />
                    <div className="h-3 bg-slate-700 rounded animate-pulse w-1/4" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty state */}
          {!isLoading && items.length === 0 && (
            <div className="flex flex-col items-center justify-center
                            h-full py-16 text-center">
              <div className="text-6xl mb-4">🛒</div>
              <h3 className="text-white font-semibold text-lg mb-2">
                Your cart is empty
              </h3>
              <p className="text-slate-400 text-sm mb-6">
                Add some products to get started.
              </p>
              <button
                onClick={closeDrawer}
                className="px-5 py-2.5 bg-violet-600 hover:bg-violet-700
                           text-white text-sm font-medium rounded-xl
                           transition-colors"
              >
                Browse Products
              </button>
            </div>
          )}

          {/* Cart items */}
          {items.length > 0 && (
            <div>
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
          )}
        </div>

        {/* ── Footer ──────────────────────────────────────────────── */}
        {items.length > 0 && (
          <div className="flex-shrink-0 px-5 py-4
                          border-t border-slate-700/50 bg-slate-900">
            <CartSummary
              subtotal={subtotal}
              itemCount={itemCount}
              onCheckout={handleCheckout}
              onClose={closeDrawer}
            />
          </div>
        )}
      </div>
    </>
  );
};

export default CartDrawer;