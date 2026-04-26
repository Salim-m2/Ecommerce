import { useQuery } from '@tanstack/react-query';
import orderAPI from '../api/orderAPI';

/**
 * Fetches the authenticated user's order list.
 * Used on the /orders (order history) page.
 *
 * staleTime: 2 minutes — order list changes only when a new order is placed
 * or a status update happens, so we don't need aggressive refetching.
 */
export const useOrders = (page = 1) => {
  return useQuery({
    queryKey:  ['orders', page],
    queryFn:   () => orderAPI.listOrders(page),
    staleTime: 2 * 60 * 1000,
    keepPreviousData: true,  // prevents flash when changing pages
  });
};

/**
 * Fetches a single order by order number.
 * Used on the /order-confirmation/{orderNumber} page.
 *
 * enabled: only runs if orderNumber is truthy — prevents a query
 * firing on initial render before the param is available.
 *
 * staleTime: 5 minutes — order detail is unlikely to change frequently
 * from the user's perspective (status changes come via the orders list).
 */
export const useOrder = (orderNumber) => {
  return useQuery({
    queryKey:  ['order', orderNumber],
    queryFn:   () => orderAPI.getOrder(orderNumber),
    enabled:   !!orderNumber,
    staleTime: 5 * 60 * 1000,
  });
};