/**
 * SearchBar component.
 *
 * Reads and writes the 'search' URL param.
 * Input is debounced at 400ms — the URL (and therefore the API call)
 * only updates after the user stops typing, not on every keystroke.
 *
 * The clear button appears when the input has text, allowing one-click reset.
 */
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, X } from 'lucide-react';
import useDebounce from '../../hooks/useDebounce';

const SearchBar = ({ placeholder = 'Search products...' }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  // Local state drives the input display immediately (feels responsive).
  // The debounced value updates the URL after the user pauses typing.
  const [inputValue, setInputValue] = useState(
    searchParams.get('search') || ''
  );
  const debouncedValue = useDebounce(inputValue, 400);

  // When the debounced value changes, update the URL param.
  useEffect(() => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev);
      if (debouncedValue) {
        next.set('search', debouncedValue);
      } else {
        next.delete('search');
      }
      next.set('page', '1'); // reset pagination on new search
      return next;
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedValue]);

  // If the URL search param is cleared externally (e.g. "Clear all filters"),
  // sync the input back to empty.
  useEffect(() => {
    const urlSearch = searchParams.get('search') || '';
    if (urlSearch !== inputValue) {
      setInputValue(urlSearch);
    }
  // Only run when the URL param changes, not on inputValue changes
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams.get('search')]);

  const handleClear = () => {
    setInputValue('');
  };

  return (
    <div className="relative w-full max-w-md">
      {/* Search icon */}
      <Search
        size={16}
        className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"
      />

      <input
        type="text"
        value={inputValue}
        onChange={e => setInputValue(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-9 pr-9 py-2 border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent transition"
      />

      {/* Clear button — only visible when input has text */}
      {inputValue && (
        <button
          onClick={handleClear}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 transition-colors"
          aria-label="Clear search"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
};

export default SearchBar;