import { Link } from 'react-router-dom';
import { ShoppingBag } from 'lucide-react';
import { formatPrice } from '../../utils/formatters';

/**
 * Shows the order summary block — subtotal, shipping note, total, and CTA.
 * Used in both the CartDrawer footer and the full Cart page sidebar.
 *
 * Props:
 *   subtotal    — number
 *   itemCount   — number (used in label)
 *   onCheckout  — fn called when "Proceed to Checkout" is clicked
 *   onClose     — optional fn to close the drawer before navigating
 */
const CartSummary = ({ subtotal, itemCount, onCheckout, onClose }) => {
  return (
    <div className="space-y-3">
      {/* Subtotal row */}
      <div className="flex justify-between items-center text-sm">
        <span className="text-slate-400">
          Subtotal ({itemCount} item{itemCount !== 1 ? 's' : ''})
        </span>
        <span className="text-white font-medium">{formatPrice(subtotal)}</span>
      </div>

      {/* Shipping row */}
      <div className="flex justify-between items-center text-sm">
        <span className="text-slate-400">Shipping</span>
        <span className="text-slate-400 italic">Calculated at checkout</span>
      </div>

      {/* Divider */}
      <div className="border-t border-slate-700 pt-3">
        {/* Total row */}
        <div className="flex justify-between items-center">
          <span className="text-white font-bold text-base">Total</span>
          <span className="text-white font-bold text-lg">
            {formatPrice(subtotal)}
          </span>
        </div>
      </div>

      {/* Checkout button */}
      <button
        onClick={onCheckout}
        className="w-full flex items-center justify-center gap-2 py-3 px-4
                   bg-violet-600 hover:bg-violet-700 active:bg-violet-800
                   text-white font-semibold rounded-xl transition-colors
                   disabled:opacity-50 disabled:cursor-not-allowed"
        disabled={itemCount === 0}
      >
        <ShoppingBag size={16} />
        Proceed to Checkout
      </button>

      {/* Continue shopping */}
      <Link
        to="/products"
        onClick={onClose}
        className="block text-center text-sm text-slate-400
                   hover:text-violet-400 transition-colors py-1"
      >
        ← Continue Shopping
      </Link>
    </div>
  );
};

export default CartSummary;