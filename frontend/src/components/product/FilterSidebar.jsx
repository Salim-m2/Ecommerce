/**
 * FilterSidebar component.
 *
 * All filter state lives in URL search params — this component reads from
 * and writes to the URL, never to local state. That means:
 * - Filters survive page refresh
 * - Filtered URLs are shareable
 * - Browser back/forward navigates filter history
 *
 * Props:
 *   categories - array from useCategories() (nested tree with children)
 *   onClose    - called when mobile close button is tapped
 *   isOpen     - controls mobile visibility
 */
import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ChevronDown, ChevronRight, X, SlidersHorizontal } from 'lucide-react';

// ── Rating options ─────────────────────────────────────────────────────────
const RATING_OPTIONS = [
  { label: '4★ & above', value: '4' },
  { label: '3★ & above', value: '3' },
  { label: '2★ & above', value: '2' },
  { label: '1★ & above', value: '1' },
];

// ── Single category row (handles expand/collapse for subcategories) ─────────
const CategoryRow = ({ category, depth = 0, onSelect, activeSlug }) => {
  const hasChildren = category.children && category.children.length > 0;
  const [expanded, setExpanded] = useState(
    // Auto-expand if any child is active
    hasChildren && category.children.some(c => c.slug === activeSlug)
  );

  const isActive = category.slug === activeSlug;

  return (
    <div>
      <div
        className={`flex items-center justify-between py-1.5 px-2 rounded-lg cursor-pointer transition-colors
          ${depth > 0 ? 'ml-3' : ''}
          ${isActive
            ? 'bg-indigo-50 text-indigo-700 font-semibold'
            : 'text-gray-700 hover:bg-gray-100'
          }`}
        style={{ paddingLeft: depth > 0 ? `${depth * 12 + 8}px` : undefined }}
        onClick={() => {
          onSelect(category.slug);
          if (hasChildren) setExpanded(e => !e);
        }}
      >
        <span className="text-sm">{category.name}</span>
        {hasChildren && (
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded(ex => !ex); }}
            className="p-0.5 text-gray-400 hover:text-gray-600"
          >
            {expanded
              ? <ChevronDown size={14} />
              : <ChevronRight size={14} />}
          </button>
        )}
      </div>

      {hasChildren && expanded && (
        <div>
          {category.children.map(child => (
            <CategoryRow
              key={child.slug}
              category={child}
              depth={depth + 1}
              onSelect={onSelect}
              activeSlug={activeSlug}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// ── Main sidebar ───────────────────────────────────────────────────────────
const FilterSidebar = ({ categories = [], isOpen, onClose }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [minPrice, setMinPrice] = useState(searchParams.get('min_price') || '');
  const [maxPrice, setMaxPrice] = useState(searchParams.get('max_price') || '');

  const activeCategory = searchParams.get('category') || '';
  const activeRating   = searchParams.get('rating')   || '';

  // ── Helpers ──────────────────────────────────────────────────────────────

  const setParam = (key, value) => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set(key, value);
      } else {
        next.delete(key);
      }
      next.set('page', '1'); // always reset to page 1 on filter change
      return next;
    });
  };

  const handleCategorySelect = (slug) => {
    // Clicking the already-active category clears it
    setParam('category', slug === activeCategory ? '' : slug);
  };

  const handlePriceApply = () => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      minPrice ? next.set('min_price', minPrice) : next.delete('min_price');
      maxPrice ? next.set('max_price', maxPrice) : next.delete('max_price');
      next.set('page', '1');
      return next;
    });
  };

  const handleRatingSelect = (value) => {
    setParam('rating', value === activeRating ? '' : value);
  };

  const handleClearAll = () => {
    setMinPrice('');
    setMaxPrice('');
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      ['category', 'min_price', 'max_price', 'rating'].forEach(k => next.delete(k));
      next.set('page', '1');
      return next;
    });
  };

  const hasActiveFilters =
    activeCategory || activeRating ||
    searchParams.get('min_price') || searchParams.get('max_price');

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-30 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={`
          fixed top-0 left-0 h-full w-72 bg-white z-40 shadow-xl overflow-y-auto
          transform transition-transform duration-300
          lg:static lg:h-auto lg:w-full lg:shadow-none lg:transform-none lg:z-auto
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b lg:hidden">
          <span className="font-semibold text-gray-900 flex items-center gap-2">
            <SlidersHorizontal size={16} /> Filters
          </span>
          <button onClick={onClose} className="p-1 text-gray-500 hover:text-gray-800">
            <X size={20} />
          </button>
        </div>

        <div className="p-4 space-y-6">

          {/* Clear all */}
          {hasActiveFilters && (
            <button
              onClick={handleClearAll}
              className="text-xs text-indigo-600 hover:text-indigo-800 font-medium underline"
            >
              Clear all filters
            </button>
          )}

          {/* Categories */}
          {categories.length > 0 && (
            <div>
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
                Categories
              </h3>
              <div className="space-y-0.5">
                {categories.map(cat => (
                  <CategoryRow
                    key={cat.slug}
                    category={cat}
                    onSelect={handleCategorySelect}
                    activeSlug={activeCategory}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Price range */}
          <div>
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
              Price Range
            </h3>
            <div className="flex items-center gap-2">
              <input
                type="number"
                placeholder="Min"
                value={minPrice}
                min={0}
                onChange={e => setMinPrice(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
              <span className="text-gray-400 text-sm">–</span>
              <input
                type="number"
                placeholder="Max"
                value={maxPrice}
                min={0}
                onChange={e => setMaxPrice(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
            </div>
            <button
              onClick={handlePriceApply}
              className="mt-2 w-full bg-indigo-600 text-white text-sm font-medium py-1.5 rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Apply
            </button>
          </div>

          {/* Minimum rating */}
          <div>
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
              Minimum Rating
            </h3>
            <div className="space-y-1">
              {RATING_OPTIONS.map(({ label, value }) => (
                <button
                  key={value}
                  onClick={() => handleRatingSelect(value)}
                  className={`w-full text-left px-2 py-1.5 rounded-lg text-sm transition-colors
                    ${activeRating === value
                      ? 'bg-indigo-50 text-indigo-700 font-semibold'
                      : 'text-gray-700 hover:bg-gray-100'
                    }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

        </div>
      </aside>
    </>
  );
};

export default FilterSidebar; 