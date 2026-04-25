import { Trash2, Minus, Plus } from 'lucide-react';
import { buildCloudinaryUrl } from '../../utils/formatters';
import { formatPrice } from '../../utils/formatters';

/**
 * Renders a single cart item row.
 * Used in both the CartDrawer and the full Cart page.
 *
 * Props:
 *   item        — CartItem object from the API
 *   itemIndex   — 0-based position in cart.items (used for update/remove calls)
 *   onRemove    — async fn(itemIndex)
 *   onUpdate    — async fn(itemIndex, newQuantity)
 *   isUpdating  — bool — shows reduced opacity while an API call is in flight
 */
const CartItem = ({ item, itemIndex, onRemove, onUpdate, isUpdating = false }) => {
  const imageUrl = item.image_url
    ? buildCloudinaryUrl(item.image_url, 80)
    : null;

  const handleDecrease = () => {
    if (item.quantity === 1) {
      onRemove(itemIndex);
    } else {
      onUpdate(itemIndex, item.quantity - 1);
    }
  };

  const handleIncrease = () => {
    onUpdate(itemIndex, item.quantity + 1);
  };

  return (
    <div
      className={`flex gap-3 py-4 border-b border-slate-700/50 transition-opacity duration-200 ${
        isUpdating ? 'opacity-50 pointer-events-none' : 'opacity-100'
      }`}
    >
      {/* Product image */}
      <div className="w-16 h-16 flex-shrink-0 rounded-lg overflow-hidden bg-slate-700">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={item.product_name}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-2xl">
            📦
          </div>
        )}
      </div>

      {/* Item details */}
      <div className="flex-1 min-w-0">
        {/* Product name */}
        <p className="text-sm font-semibold text-white leading-tight truncate">
          {item.product_name}
        </p>

        {/* Variant details */}
        {(item.color || item.size) && (
          <p className="text-xs text-slate-400 mt-0.5">
            {[item.color, item.size ? `Size ${item.size}` : null]
              .filter(Boolean)
              .join(' / ')}
          </p>
        )}

        {/* Price per unit */}
        <p className="text-xs text-slate-400 mt-0.5">
          {formatPrice(item.price_at_add)} each
        </p>

        {/* Quantity controls + line total */}
        <div className="flex items-center justify-between mt-2">
          {/* Quantity control */}
          <div className="flex items-center gap-1 bg-slate-700 rounded-lg p-0.5">
            <button
              onClick={handleDecrease}
              className="w-6 h-6 flex items-center justify-center rounded-md
                         text-slate-300 hover:bg-slate-600 hover:text-white
                         transition-colors"
              aria-label="Decrease quantity"
            >
              <Minus size={12} />
            </button>

            <span className="w-6 text-center text-sm font-medium text-white">
              {item.quantity}
            </span>

            <button
              onClick={handleIncrease}
              className="w-6 h-6 flex items-center justify-center rounded-md
                         text-slate-300 hover:bg-slate-600 hover:text-white
                         transition-colors"
              aria-label="Increase quantity"
            >
              <Plus size={12} />
            </button>
          </div>

          {/* Line total */}
          <p className="text-sm font-bold text-white">
            {formatPrice(item.price_at_add * item.quantity)}
          </p>
        </div>
      </div>

      {/* Remove button */}
      <button
        onClick={() => onRemove(itemIndex)}
        className="flex-shrink-0 self-start p-1.5 text-slate-500
                   hover:text-red-400 transition-colors rounded-md
                   hover:bg-red-400/10"
        aria-label="Remove item"
      >
        <Trash2 size={14} />
      </button>
    </div>
  );
};

export default CartItem;