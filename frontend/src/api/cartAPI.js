import api from './axiosInstance';

// ─────────────────────────────────────────────────────────────────────────────
// Guest session key helpers
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Returns the guest session key from localStorage, or null if not set.
 * Exported so authSlice can read it during cart merge on login.
 */
export const getSessionKey = () => localStorage.getItem('guest_session_key');

/**
 * Generates a UUID v4, saves it to localStorage, and returns it.
 * Uses the browser's built-in crypto API — no library needed.
 */
export const ensureSessionKey = () => {
  let key = getSessionKey();
  if (!key) {
    key = crypto.randomUUID();
    localStorage.setItem('guest_session_key', key);
  }
  return key;
};

/**
 * Builds the X-Session-Key header object if a guest session key exists.
 * Returns an empty object for logged-in users so the header is simply omitted.
 */
const sessionHeader = () => {
  const key = getSessionKey();
  return key ? { 'X-Session-Key': key } : {};
};

// ─────────────────────────────────────────────────────────────────────────────
// Cart API calls
// All functions return response.data directly so callers get clean objects.
// withCredentials: true is set globally on the axiosInstance, so JWT cookies
// are sent automatically on every request without any extra config here.
// ─────────────────────────────────────────────────────────────────────────────

const cartAPI = {
  /**
   * Fetches the current cart.
   * Works for both guests (sends X-Session-Key) and logged-in users (sends JWT cookie).
   */
  getCart: async () => {
    const response = await api.get('/cart/', { headers: sessionHeader() });
    return response.data;
  },

  /**
   * Adds an item to the cart.
   * ensureSessionKey() is called by the useCart hook BEFORE this is called,
   * so the key is guaranteed to exist in localStorage when this runs.
   */
  addItem: async ({ product_id, variant_id, quantity }) => {
    const response = await api.post(
      '/cart/items/',
      { product_id, variant_id, quantity },
      { headers: sessionHeader() },
    );
    return response.data;
  },

  /**
   * Updates the quantity of a cart item at the given index.
   * itemIndex is the 0-based position in the cart.items array.
   */
  updateItem: async (itemIndex, quantity) => {
    const response = await api.patch(
      `/cart/items/${itemIndex}/`,
      { quantity },
      { headers: sessionHeader() },
    );
    return response.data;
  },

  /**
   * Removes the cart item at the given index entirely.
   */
  removeItem: async (itemIndex) => {
    const response = await api.delete(
      `/cart/items/${itemIndex}/`,
      { headers: sessionHeader() },
    );
    return response.data;
  },

  /**
   * Merges the guest cart into the logged-in user's cart.
   * Called immediately after a successful login.
   * No session header needed here — the user is already authenticated via JWT cookie.
   */
  mergeCart: async (sessionKey) => {
    const response = await api.post('/cart/merge/', { session_key: sessionKey });
    return response.data;
  },

  /**
   * Applies a coupon code to the cart.
   * Returns a placeholder message until Week 10 when real coupon logic is added.
   */
  applyCoupon: async (couponCode) => {
    const response = await api.post(
      '/cart/coupon/',
      { coupon_code: couponCode },
      { headers: sessionHeader() },
    );
    return response.data;
  },
};

export default cartAPI;