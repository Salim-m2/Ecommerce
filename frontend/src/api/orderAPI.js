import api from './axiosInstance';

/**
 * All order and payment API calls.
 * Uses the shared axiosInstance which has withCredentials: true
 * so httpOnly JWT cookies are sent automatically on every request.
 */

const orderAPI = {
  /**
   * POST /orders/
   * Creates an order from the user's current cart.
   * Body: { shipping_address, shipping_method, notes }
   * Returns the full created Order object.
   */
  createOrder: async (data) => {
    const response = await api.post('/orders/', data);
    return response.data;
  },

  /**
   * GET /orders/?page={page}&page_size={pageSize}
   * Returns the authenticated user's orders, newest first.
   * Response shape: { count, total_pages, current_page, page_size, results }
   */
  listOrders: async (page = 1, pageSize = 10) => {
    const response = await api.get('/orders/', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  /**
   * GET /orders/{orderNumber}/
   * Returns the full order detail for the given order number.
   * The backend enforces ownership — other users' orders return 404.
   */
  getOrder: async (orderNumber) => {
    const response = await api.get(`/orders/${orderNumber}/`);
    return response.data;
  },

  /**
   * POST /payments/initialize/
   * Creates an IntaSend hosted checkout session for the given order.
   * Returns { payment_url, checkout_id, order_number }
   * The frontend redirects the user to payment_url.
   */
  initializePayment: async (orderId) => {
    const response = await api.post('/payments/initialize/', { order_id: orderId });
    return response.data;
  },

  /**
   * POST /payments/verify/
   * Called after IntaSend redirects the user back to the app.
   * Verifies the payment server-side before marking the order as paid.
   * Body: { checkout_id, invoice_id }
   * Returns { status, order_number }
   */
  verifyPayment: async ({ checkoutId, invoiceId }) => {
    const response = await api.post('/payments/verify/', {
      checkout_id: checkoutId,
      invoice_id:  invoiceId,
    });
    return response.data;
  },

  // DEV ONLY — remove before production
  devConfirmPayment: async (orderId) => {
    const response = await api.post('/payments/dev-confirm/', { order_id: orderId });
    return response.data;
  },
};

export default orderAPI;