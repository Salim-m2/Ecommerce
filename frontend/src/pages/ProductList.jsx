/**
 * ProductList page — the main product browsing experience.
 *
 * ALL filter state lives in URL search params, never in component state.
 * This gives us:
 * - Shareable filtered URLs (/products?category=sneakers&sort=price_asc)
 * - Browser back/forward navigates filter history
 * - Refreshing the page preserves filters
 * - Deep-linking from the Navbar search works automatically
 */
import { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { SlidersHorizontal } from 'lucide-react';

import { useProducts } from '../hooks/useProducts';
import { useCategories } from '../hooks/useProducts';
import ProductGrid from '../components/product/ProductGrid';
import FilterSidebar from '../components/product/FilterSidebar';
import SortDropdown from '../components/product/SortDropdown';
import SearchBar from '../components/product/SearchBar';
import Pagination from '../components/ui/Pagination';

const PAGE_SIZE = 12;

const ProductList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // ── Read all filter state from URL ──────────────────────────────────────
  const filters = {
    category:  searchParams.get('category')  || undefined,
    min_price: searchParams.get('min_price') || undefined,
    max_price: searchParams.get('max_price') || undefined,
    rating:    searchParams.get('rating')    || undefined,
    search:    searchParams.get('search')    || undefined,
    sort:      searchParams.get('sort')      || 'newest',
    page:      parseInt(searchParams.get('page') || '1', 10),
    page_size: PAGE_SIZE,
  };

  // ── Data fetching ────────────────────────────────────────────────────────
  const { data, isLoading, isError } = useProducts(filters);
  const { data: categories = [] }    = useCategories();

  const products    = data?.results     || [];
  const totalPages  = data?.total_pages || 1;
  const totalCount  = data?.count       || 0;
  const currentPage = data?.current_page || filters.page;

  // ── Update helpers ───────────────────────────────────────────────────────

  const setSort = (value) => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      next.set('sort', value);
      next.set('page', '1');
      return next;
    });
  };

  const setPage = (page) => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      next.set('page', String(page));
      return next;
    });
  };

  // ── Result count string: "Showing 1–12 of 38 results" ───────────────────
  const from = totalCount === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1;
  const to   = Math.min(currentPage * PAGE_SIZE, totalCount);
  const resultLabel = totalCount === 0
    ? 'No products found'
    : `Showing ${from}–${to} of ${totalCount} result${totalCount !== 1 ? 's' : ''}`;

  // ── Active filter count (for mobile badge) ───────────────────────────────
  const activeFilterCount = [
    searchParams.get('category'),
    searchParams.get('min_price'),
    searchParams.get('max_price'),
    searchParams.get('rating'),
  ].filter(Boolean).length;

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-screen-xl mx-auto px-4 py-6">

        {/* Top bar: search + mobile filter button */}
        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1">
            <SearchBar placeholder="Search products..." />
          </div>

          {/* Mobile filter toggle */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-xl bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 relative"
          >
            <SlidersHorizontal size={16} />
            Filters
            {activeFilterCount > 0 && (
              <span className="absolute -top-1.5 -right-1.5 bg-indigo-600 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>

        {/* Main layout: sidebar + grid */}
        <div className="flex gap-6">

          {/* Sidebar — hidden on mobile (shown as drawer), visible on lg+ */}
          <div className="hidden lg:block w-56 flex-shrink-0">
            <FilterSidebar
              categories={categories}
              isOpen={sidebarOpen}
              onClose={() => setSidebarOpen(false)}
            />
          </div>

          {/* Mobile sidebar drawer */}
          <div className="lg:hidden">
            <FilterSidebar
              categories={categories}
              isOpen={sidebarOpen}
              onClose={() => setSidebarOpen(false)}
            />
          </div>

          {/* Product area */}
          <div className="flex-1 min-w-0">

            {/* Sort row + result count */}
            <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
              <p className="text-sm text-gray-500">{resultLabel}</p>
              <SortDropdown
                value={filters.sort}
                onChange={setSort}
              />
            </div>

            {/* Error state */}
            {isError && (
              <div className="text-center py-16 text-gray-500">
                <p className="text-lg font-medium">Something went wrong.</p>
                <p className="text-sm mt-1">Please try again.</p>
              </div>
            )}

            {/* Empty state */}
            {!isLoading && !isError && products.length === 0 && (
              <div className="text-center py-16 text-gray-500">
                <p className="text-4xl mb-3">🔍</p>
                <p className="text-lg font-medium text-gray-700">No products found</p>
                <p className="text-sm mt-1 mb-4">
                  Try adjusting your filters or search term.
                </p>
                <Link
                  to="/products"
                  className="inline-block px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Clear filters
                </Link>
              </div>
            )}

            {/* Product grid */}
            {!isError && (
              <ProductGrid
                products={products}
                isLoading={isLoading}
                skeletonCount={PAGE_SIZE}
              />
            )}

            {/* Pagination */}
            {!isLoading && totalPages > 1 && (
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={setPage}
              />
            )}

          </div>
        </div>

      </div>
    </div>
  );
};

export default ProductList;