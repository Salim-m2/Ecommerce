/**
 * Product catalog API calls.
 *
 * All functions use the shared axiosInstance which:
 * - Has withCredentials: true (sends httpOnly cookies automatically)
 * - Has the 401 → silent refresh interceptor
 * - Uses baseURL '/api/v1'
 */
import api from './axiosInstance';

/**
 * Build a query string from a filters object.
 * Skips null, undefined, and empty string values so we never send
 * ?category=&min_price= to the backend.
 */
const buildQueryString = (filters = {}) => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      params.set(key, value);
    }
  });
  return params.toString();
};

const productAPI = {
  /**
   * GET /products/?category=...&min_price=...&sort=...&page=...
   * Returns { count, total_pages, current_page, page_size, results }
   */
  list: async (filters = {}) => {
    const qs = buildQueryString(filters);
    const url = qs ? `/products/?${qs}` : '/products/';
    const response = await api.get(url);
    return response.data;
  },

  /**
   * GET /products/{slug}/
   * Returns full product document with all variants.
   */
  getBySlug: async (slug) => {
    const response = await api.get(`/products/${slug}/`);
    return response.data;
  },

  /**
   * GET /categories/
   * Returns nested category tree: top-level categories with children arrays.
   */
  getCategories: async () => {
    const response = await api.get('/categories/');
    return response.data;
  },

  /**
   * POST /products/upload-image/
   * Requires admin or seller role. Accepts a File object + product slug.
   * Returns { url, public_id }
   */
  uploadImage: async (file, productSlug) => {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('product_slug', productSlug);
    const response = await api.post('/products/upload-image/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

export default productAPI;