import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ShoppingBag, Package, ChevronLeft, ChevronRight } from 'lucide-react';

import { useOrders } from '../../hooks/useOrders';
import { formatPrice } from '../../utils/formatters';

// ── Status badge config ───────────────────────────────────────────────────────
const STATUS_CONFIG = {
  pending:    { label: 'Pending',    styles: 'bg-yellow-500/10 text-yellow-400  border-yellow-500/30'  },
  paid:       { label: 'Paid',       styles: 'bg-blue-500/10   text-blue-400    border-blue-500/30'    },
  processing: { label: 'Processing', styles: 'bg-indigo-500/10 text-indigo-400  border-indigo-500/30'  },
  shipped:    { label: 'Shipped',    styles: 'bg-violet-500/10 text-violet-400  border-violet-500/30'  },
  delivered:  { label: 'Delivered',  styles: 'bg-green-500/10  text-green-400   border-green-500/30'   },
  cancelled:  { label: 'Cancelled',  styles: 'bg-red-500/10    text-red-400     border-red-500/30'     },
  refunded:   { label: 'Refunded',   styles: 'bg-orange-500/10 text-orange-400  border-orange-500/30'  },
};

const FILTER_TABS = ['all', 'pending', 'paid', 'processing', 'shipped', 'delivered'];

function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  return (
    <span className={`
      inline-flex items-center px-2.5 py-0.5 rounded-full
      text-xs font-semibold border ${config.styles}
    `}>
      {config.label}
    </span>
  );
}

// ── Skeleton loader ───────────────────────────────────────────────────────────
function OrderCardSkeleton() {
  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-5 animate-pulse">
      <div className="flex items-center justify-between mb-4">
        <div className="h-4 w-32 bg-slate-700 rounded" />
        <div className="h-5 w-20 bg-slate-700 rounded-full" />
      </div>
      <div className="flex items-center gap-3 mb-4">
        <div className="w-14 h-14 rounded-xl bg-slate-700 flex-shrink-0" />
        <div className="space-y-2 flex-1">
          <div className="h-3.5 w-48 bg-slate-700 rounded" />
          <div className="h-3 w-24 bg-slate-700 rounded" />
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="h-4 w-20 bg-slate-700 rounded" />
        <div className="h-8 w-24 bg-slate-700 rounded-xl" />
      </div>
    </div>
  );
}

// ── Pagination ────────────────────────────────────────────────────────────────
function Pagination({ currentPage, totalPages, onPageChange }) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-2 mt-8">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="p-2 rounded-lg border border-slate-700 text-slate-400
                   hover:border-slate-500 hover:text-slate-200
                   disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        <ChevronLeft size={16} />
      </button>

      {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
        <button
          key={page}
          onClick={() => onPageChange(page)}
          className={`
            w-9 h-9 rounded-lg text-sm font-medium transition-colors
            ${page === currentPage
              ? 'bg-violet-600 text-white'
              : 'border border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200'}
          `}
        >
          {page}
        </button>
      ))}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="p-2 rounded-lg border border-slate-700 text-slate-400
                   hover:border-slate-500 hover:text-slate-200
                   disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        <ChevronRight size={16} />
      </button>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function Orders() {
  const [activeTab,    setActiveTab]    = useState('all');
  const [currentPage,  setCurrentPage]  = useState(1);

  const { data, isLoading, isError } = useOrders(currentPage);

  const allOrders   = data?.results ?? [];
  const totalPages  = data?.total_pages ?? 1;

  // Filter client-side — the full page is small enough that we don't need
  // a separate API call per tab. If the user has hundreds of orders we'd
  // add a ?status= filter to the API call instead.
  const filteredOrders = activeTab === 'all'
    ? allOrders
    : allOrders.filter(order => order.status === activeTab);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setCurrentPage(1);  // reset page when switching tabs
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-slate-950 py-10 px-4">
      <div className="max-w-3xl mx-auto">

        {/* Page header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">My Orders</h1>
          <p className="text-slate-400 text-sm mt-1">
            Track and manage your order history
          </p>
        </div>

        {/* Filter tabs */}
        <div className="flex items-center gap-1 mb-6 overflow-x-auto pb-1">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => handleTabChange(tab)}
              className={`
                px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-colors
                ${activeTab === tab
                  ? 'bg-violet-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'}
              `}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* ── Loading state ─────────────────────────────────────────── */}
        {isLoading && (
          <div className="space-y-4">
            {[1, 2, 3].map(i => <OrderCardSkeleton key={i} />)}
          </div>
        )}

        {/* ── Error state ───────────────────────────────────────────── */}
        {isError && !isLoading && (
          <div className="text-center py-16">
            <p className="text-slate-400">Failed to load orders. Please try again.</p>
          </div>
        )}

        {/* ── Empty state ───────────────────────────────────────────── */}
        {!isLoading && !isError && filteredOrders.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-4">
              <ShoppingBag size={28} className="text-slate-600" />
            </div>
            <h3 className="text-white font-semibold mb-2">
              {activeTab === 'all' ? 'No orders yet' : `No ${activeTab} orders`}
            </h3>
            <p className="text-slate-500 text-sm mb-6">
              {activeTab === 'all'
                ? "You haven't placed any orders yet."
                : `You have no orders with status "${activeTab}".`}
            </p>
            {activeTab === 'all' && (
              <Link
                to="/products"
                className="px-6 py-2.5 bg-violet-600 hover:bg-violet-700
                           text-white font-semibold rounded-xl text-sm transition-colors"
              >
                Start Shopping
              </Link>
            )}
          </div>
        )}

        {/* ── Order cards ───────────────────────────────────────────── */}
        {!isLoading && !isError && filteredOrders.length > 0 && (
          <>
            <div className="space-y-4">
              {filteredOrders.map((order) => (
                <OrderCard key={order.id} order={order} />
              ))}
            </div>

            <Pagination
              currentPage  = {currentPage}
              totalPages   = {totalPages}
              onPageChange = {handlePageChange}
            />
          </>
        )}

      </div>
    </div>
  );
}

// ── Order card component ──────────────────────────────────────────────────────
function OrderCard({ order }) {
  // Format the date cleanly — e.g. "Apr 26, 2025"
  const formattedDate = new Date(order.created_at).toLocaleDateString('en-KE', {
    year:  'numeric',
    month: 'short',
    day:   'numeric',
  });

  const hasMultipleItems = order.item_count > 1;

  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-5
                    hover:border-slate-600 transition-colors">

      {/* Top row — order number + date + status */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <span className="text-violet-400 font-mono font-bold text-sm">
            {order.order_number}
          </span>
          <p className="text-slate-500 text-xs mt-0.5">{formattedDate}</p>
        </div>
        <StatusBadge status={order.status} />
      </div>

      {/* Item preview */}
      <div className="flex items-center gap-3 mb-5">
        {order.first_item_image ? (
          <img
            src={order.first_item_image}
            alt="Order item"
            className="w-14 h-14 rounded-xl object-cover bg-slate-700 flex-shrink-0"
          />
        ) : (
          <div className="w-14 h-14 rounded-xl bg-slate-700 flex-shrink-0
                          flex items-center justify-center">
            <Package size={20} className="text-slate-500" />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-200">
            {hasMultipleItems
              ? `${order.item_count} items`
              : '1 item'}
          </p>
          <p className="text-xs text-slate-500 mt-0.5">
            {order.item_count === 1
              ? 'View details for product info'
              : `${order.item_count} items in this order`}
          </p>
        </div>
      </div>

      {/* Bottom row — total + action button */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-500 mb-0.5">Total</p>
          <p className="text-base font-bold text-white">
            {formatPrice(order.total)}
          </p>
        </div>
        <Link
          to={`/order-confirmation/${order.order_number}`}
          className="px-4 py-2 bg-slate-700 hover:bg-slate-600
                     text-slate-200 hover:text-white
                     text-sm font-medium rounded-xl transition-colors"
        >
          View Details
        </Link>
      </div>
    </div>
  );
}