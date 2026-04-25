import { useDispatch, useSelector } from 'react-redux';
import {
  selectCart,
  selectCartItems,
  selectCartItemCount,
  selectCartSubtotal,
  selectCartIsOpen,
  selectCartIsLoading,
  openCartDrawer,
  closeCartDrawer,
  toggleCartDrawer,
  addToCart,
  updateCartItem,
  removeFromCart,
} from '../store/cartSlice';

/**
 * useCart — the single hook every component uses to read and mutate cart state.
 *
 * Returns both state (from Redux) and action dispatchers so components never
 * need to import from cartSlice directly.
 *
 * addToCart automatically opens the drawer on success so the user can see
 * what they just added without navigating away from the product page.
 */
const useCart = () => {
  const dispatch = useDispatch();

  const cart      = useSelector(selectCart);
  const items     = useSelector(selectCartItems);
  const itemCount = useSelector(selectCartItemCount);
  const subtotal  = useSelector(selectCartSubtotal);
  const isOpen    = useSelector(selectCartIsOpen);
  const isLoading = useSelector(selectCartIsLoading);

  /**
   * Adds an item to the cart.
   * Returns { success: true } or { success: false, error: string }.
   * The drawer opens automatically via the addToCart.fulfilled reducer.
   */
  const addItem = async (product_id, variant_id, quantity = 1) => {
    const result = await dispatch(addToCart({ product_id, variant_id, quantity }));
    if (addToCart.fulfilled.match(result)) {
      return { success: true };
    }
    return { success: false, error: result.payload };
  };

  /**
   * Updates the quantity of the item at itemIndex.
   * Returns { success: true } or { success: false, error: string }.
   */
  const updateItem = async (itemIndex, quantity) => {
    const result = await dispatch(updateCartItem({ itemIndex, quantity }));
    if (updateCartItem.fulfilled.match(result)) {
      return { success: true };
    }
    return { success: false, error: result.payload };
  };

  /**
   * Removes the item at itemIndex from the cart.
   * Returns { success: true } or { success: false, error: string }.
   */
  const removeItem = async (itemIndex) => {
    const result = await dispatch(removeFromCart(itemIndex));
    if (removeFromCart.fulfilled.match(result)) {
      return { success: true };
    }
    return { success: false, error: result.payload };
  };

  return {
    // State
    cart,
    items,
    itemCount,
    subtotal,
    isOpen,
    isLoading,

    // Cart mutations
    addItem,
    updateItem,
    removeItem,

    // Drawer controls
    openDrawer:   () => dispatch(openCartDrawer()),
    closeDrawer:  () => dispatch(closeCartDrawer()),
    toggleDrawer: () => dispatch(toggleCartDrawer()),
  };
};

export default useCart;