import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import cartAPI, { ensureSessionKey, getSessionKey } from '../api/cartAPI';

// ─────────────────────────────────────────────────────────────────────────────
// Async thunks
// Each thunk calls the API and returns the updated cart object on success.
// Redux Toolkit automatically dispatches pending / fulfilled / rejected actions.
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Fetches the current cart on app startup and after mutations.
 * Dispatched in main.jsx so the navbar badge is correct on every page load.
 */
export const fetchCart = createAsyncThunk(
  'cart/fetch',
  async (_, { rejectWithValue }) => {
    try {
      return await cartAPI.getCart();
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to load cart.');
    }
  },
);

/**
 * Adds an item to the cart.
 * ensureSessionKey() runs first so guests always have a session key before
 * the API call — the backend requires it for guest carts.
 */
export const addToCart = createAsyncThunk(
  'cart/addItem',
  async ({ product_id, variant_id, quantity }, { rejectWithValue }) => {
    try {
      ensureSessionKey(); // creates key if not present
      return await cartAPI.addItem({ product_id, variant_id, quantity });
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to add item.');
    }
  },
);

/**
 * Updates the quantity of an existing cart item.
 */
export const updateCartItem = createAsyncThunk(
  'cart/updateItem',
  async ({ itemIndex, quantity }, { rejectWithValue }) => {
    try {
      return await cartAPI.updateItem(itemIndex, quantity);
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to update item.');
    }
  },
);

/**
 * Removes an item from the cart.
 */
export const removeFromCart = createAsyncThunk(
  'cart/removeItem',
  async (itemIndex, { rejectWithValue }) => {
    try {
      return await cartAPI.removeItem(itemIndex);
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to remove item.');
    }
  },
);

/**
 * Merges the guest cart into the user's cart immediately after login.
 * After a successful merge, the guest session key is deleted from localStorage
 * — the user now has an authenticated cart and no longer needs a guest key.
 */
export const mergeCart = createAsyncThunk(
  'cart/merge',
  async (sessionKey, { rejectWithValue }) => {
    try {
      const cart = await cartAPI.mergeCart(sessionKey);
      // Guest key has been absorbed — delete it so future requests use the JWT
      localStorage.removeItem('guest_session_key');
      return cart;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to merge cart.');
    }
  },
);

// ─────────────────────────────────────────────────────────────────────────────
// Slice
// ─────────────────────────────────────────────────────────────────────────────

const cartSlice = createSlice({
  name: 'cart',
  initialState: {
    cart: null,       // the full cart object returned by the API
    isLoading: false,
    isOpen: false,    // controls the cart drawer (sidebar)
    error: null,
  },
  reducers: {
    // Drawer controls — dispatched from Navbar and CartDrawer
    openCartDrawer:   (state) => { state.isOpen = true; },
    closeCartDrawer:  (state) => { state.isOpen = false; },
    toggleCartDrawer: (state) => { state.isOpen = !state.isOpen; },

    // Called on logout to wipe cart from the UI immediately
    clearCart: (state) => { state.cart = null; },
  },
  extraReducers: (builder) => {
    // ── fetchCart ──────────────────────────────────────────────────────
    builder
      .addCase(fetchCart.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchCart.fulfilled, (state, action) => {
        state.isLoading = false;
        state.cart = action.payload;
      })
      .addCase(fetchCart.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      });

    // ── addToCart ──────────────────────────────────────────────────────
    builder
      .addCase(addToCart.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(addToCart.fulfilled, (state, action) => {
        state.isLoading = false;
        state.cart = action.payload;   // backend returns updated cart
        state.isOpen = true;           // open drawer automatically
      })
      .addCase(addToCart.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      });

    // ── updateCartItem ─────────────────────────────────────────────────
    builder
      .addCase(updateCartItem.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(updateCartItem.fulfilled, (state, action) => {
        state.isLoading = false;
        state.cart = action.payload;
      })
      .addCase(updateCartItem.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      });

    // ── removeFromCart ─────────────────────────────────────────────────
    builder
      .addCase(removeFromCart.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(removeFromCart.fulfilled, (state, action) => {
        state.isLoading = false;
        state.cart = action.payload;
      })
      .addCase(removeFromCart.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      });

    // ── mergeCart ──────────────────────────────────────────────────────
    builder
      .addCase(mergeCart.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(mergeCart.fulfilled, (state, action) => {
        state.isLoading = false;
        state.cart = action.payload;
      })
      .addCase(mergeCart.rejected, (state, action) => {
        state.isLoading = false;
        // Merge failure is non-fatal — log it but don't block the user
        state.error = action.payload;
      });
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Actions
// ─────────────────────────────────────────────────────────────────────────────
export const {
  openCartDrawer,
  closeCartDrawer,
  toggleCartDrawer,
  clearCart,
} = cartSlice.actions;

// ─────────────────────────────────────────────────────────────────────────────
// Selectors
// All selectors use optional chaining so they return safe defaults
// when the cart hasn't loaded yet (state.cart.cart === null).
// ─────────────────────────────────────────────────────────────────────────────
export const selectCart         = (state) => state.cart.cart;
export const selectCartItems    = (state) => state.cart.cart?.items    ?? [];
export const selectCartItemCount= (state) => state.cart.cart?.item_count ?? 0;
export const selectCartSubtotal = (state) => state.cart.cart?.subtotal  ?? 0;
export const selectCartIsOpen   = (state) => state.cart.isOpen;
export const selectCartIsLoading= (state) => state.cart.isLoading;

export default cartSlice.reducer;