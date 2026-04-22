/**
 * SortDropdown component.
 *
 * A simple native <select> for choosing the sort order.
 * Native select is used deliberately — it has better mobile UX than a
 * custom dropdown (no positioning bugs, keyboard accessible, touch-friendly).
 *
 * Props:
 *   value    - current sort value string (e.g. 'price_asc')
 *   onChange - callback(newValue: string)
 */
const SORT_OPTIONS = [
  { label: 'Newest First',       value: 'newest'     },
  { label: 'Price: Low to High', value: 'price_asc'  },
  { label: 'Price: High to Low', value: 'price_desc' },
  { label: 'Highest Rated',      value: 'rating'     },
  { label: 'Most Popular',       value: 'popular'    },
];

const SortDropdown = ({ value = 'newest', onChange }) => {
  return (
    <div className="flex items-center gap-2">
      <label
        htmlFor="sort-select"
        className="text-sm text-gray-500 whitespace-nowrap"
      >
        Sort by
      </label>
      <select
        id="sort-select"
        value={value}
        onChange={e => onChange(e.target.value)}
        className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300 cursor-pointer"
      >
        {SORT_OPTIONS.map(({ label, value: v }) => (
          <option key={v} value={v}>{label}</option>
        ))}
      </select>
    </div>
  );
};

export default SortDropdown;