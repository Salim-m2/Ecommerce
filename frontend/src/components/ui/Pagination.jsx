/**
 * Pagination component.
 *
 * Shows Previous / page numbers with ellipsis / Next.
 * On page click, scrolls back to the top of the page smoothly.
 *
 * Props:
 *   currentPage  - 1-indexed current page number
 *   totalPages   - total number of pages
 *   onPageChange - callback(pageNumber: number)
 */
import { ChevronLeft, ChevronRight } from 'lucide-react';

/**
 * Build the array of page numbers to display, with null as an ellipsis marker.
 * For 10 pages with current=6:  [1, null, 5, 6, 7, null, 10]
 */
const buildPageNumbers = (current, total) => {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  const pages = [];
  // Always show first and last page
  // Show 2 pages around the current page
  const around = new Set([1, total, current - 1, current, current + 1]
    .filter(p => p >= 1 && p <= total));

  let prev = null;
  for (const page of [...around].sort((a, b) => a - b)) {
    if (prev !== null && page - prev > 1) {
      pages.push(null); // null = ellipsis
    }
    pages.push(page);
    prev = page;
  }

  return pages;
};

const Pagination = ({ currentPage, totalPages, onPageChange }) => {
  if (totalPages <= 1) return null;

  const pages = buildPageNumbers(currentPage, totalPages);

  const handleClick = (page) => {
    if (page === currentPage) return;
    onPageChange(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const btnBase =
    'flex items-center justify-center w-9 h-9 rounded-lg text-sm font-medium transition-colors';

  return (
    <div className="flex items-center justify-center gap-1 mt-8">

      {/* Previous */}
      <button
        onClick={() => handleClick(currentPage - 1)}
        disabled={currentPage === 1}
        className={`${btnBase} ${
          currentPage === 1
            ? 'text-gray-300 cursor-not-allowed'
            : 'text-gray-600 hover:bg-gray-100'
        }`}
        aria-label="Previous page"
      >
        <ChevronLeft size={16} />
      </button>

      {/* Page numbers */}
      {pages.map((page, index) =>
        page === null ? (
          <span key={`ellipsis-${index}`} className="w-9 text-center text-gray-400 text-sm">
            …
          </span>
        ) : (
          <button
            key={page}
            onClick={() => handleClick(page)}
            className={`${btnBase} ${
              page === currentPage
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
            aria-current={page === currentPage ? 'page' : undefined}
          >
            {page}
          </button>
        )
      )}

      {/* Next */}
      <button
        onClick={() => handleClick(currentPage + 1)}
        disabled={currentPage === totalPages}
        className={`${btnBase} ${
          currentPage === totalPages
            ? 'text-gray-300 cursor-not-allowed'
            : 'text-gray-600 hover:bg-gray-100'
        }`}
        aria-label="Next page"
      >
        <ChevronRight size={16} />
      </button>

    </div>
  );
};

export default Pagination;