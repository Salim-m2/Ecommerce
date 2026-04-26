import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { ShoppingBag } from 'lucide-react';
import { closeCartDrawer } from '../../store/cartSlice';
import { formatPrice } from '../../utils/formatters';

/**
 * Order summary panel used in both CartDrawer and the full Cart page.
 * Props:
 *   subtotal  — numeric total of all items
 *   itemCount — total number of individual items (sum of quantities)
 */
export default function CartSummary({ subtotal, itemCount }) {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const handleCheckout = () => {
    // Close the drawer first (if open) before navigating
    dispatch(closeCartDrawer());
    navigate('/checkout');
  };

  return (
    <div className="p-4 space-y-3">
      {/* Subtotal row */}
      <div className="flex justify-between text-sm text-slate-400">
        <span>
          Subtotal ({itemCount} item{itemCount !== 1 ? 's' : ''})
        </span>
        <span>{formatPrice(subtotal)}</span>
      </div>

      {/* Shipping row */}
      <div className="flex justify-between text-sm text-slate-400">
        <span>Shipping</span>
        <span className="text-slate-500">Calculated at checkout</span>
      </div>

      {/* Divider */}
      <div className="border-t border-slate-700 pt-3">
        {/* Total row */}
        <div className="flex justify-between text-base font-semibold text-white">
          <span>Total</span>
          <span>{formatPrice(subtotal)}</span>
        </div>
      </div>

      {/* Checkout button */}
      <button
        onClick={handleCheckout}
        className="w-full py-3.5 bg-violet-600 hover:bg-violet-700
                   text-white font-semibold rounded-xl
                   flex items-center justify-center gap-2
                   transition-colors mt-2"
      >
        <ShoppingBag size={16} />
        Proceed to Checkout
      </button>

      {/* Continue shopping */}
      <button
        onClick={() => { dispatch(closeCartDrawer()); navigate('/products'); }}
        className="w-full py-2 text-sm text-slate-400 hover:text-slate-200
                   transition-colors text-center"
      >
        Continue Shopping
      </button>
    </div>
  );
}