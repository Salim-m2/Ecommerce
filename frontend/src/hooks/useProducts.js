/**
 * TanStack Query hooks for product catalog data.
 *
 * Why TanStack Query instead of useEffect?
 * - Automatic caching: the same product list isn't re-fetched on every render
 * - keepPreviousData: no flash/blank state when changing pages or filters
 * - staleTime: matches the backend Redis cache TTL so we don't over-fetch
 * - Background refetch: data stays fresh without manual polling
 */
import { useQuery } from '@tanstack/react-query';
import productAPI from '../api/productAPI';

/**
 * Fetch a paginated, filtered product list.
 *
 * @param {object} filters - Any combination of:
 *   category, min_price, max_price, rating, search, sort, page, page_size
 *
 * queryKey includes the full filters object so any filter change triggers
 * a new fetch automatically. React Query deduplicates concurrent calls
 * with identical keys.
 */
export const useProducts = (filters = {}) => {
  return useQuery({
    queryKey: ['products', filters],
    queryFn:  () => productAPI.list(filters),
    // Keep the previous page's data visible while the next page loads.
    // This prevents the product grid from going blank during pagination.
    placeholderData: (previousData) => previousData,
    // 5 minutes — matches the backend Redis cache TTL for product lists.
    // Data older than this is refetched in the background on next access.
    staleTime: 5 * 60 * 1000,
  });
};

/**
 * Fetch a single product by its URL slug.
 *
 * @param {string} slug - Product slug from the URL, e.g. 'air-jordan-1-retro'
 *
 * enabled: false when slug is falsy so the query doesn't fire on initial
 * render before the router has parsed the URL param.
 */
export const useProduct = (slug) => {
  return useQuery({
    queryKey: ['product', slug],
    queryFn:  () => productAPI.getBySlug(slug),
    enabled:  !!slug,
    staleTime: 5 * 60 * 1000,
  });
};

/**
 * Fetch the full category tree.
 *
 * staleTime is 1 hour — matches the backend cache TTL for categories,
 * which almost never change. This means a user browsing the site for an
 * hour never makes a second categories request.
 */
export const useCategories = () => {
  return useQuery({
    queryKey: ['categories'],
    queryFn:  productAPI.getCategories,
    staleTime: 60 * 60 * 1000,
  });
};