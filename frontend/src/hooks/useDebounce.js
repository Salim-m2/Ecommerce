/**
 * Delays updating a value until the user stops typing.
 * Used by SearchBar to avoid firing an API call on every keystroke.
 *
 * useDebounce('nike', 400) returns 'nike' only after the user
 * hasn't typed for 400ms.
 */
import { useState, useEffect } from 'react';

const useDebounce = (value, delay = 400) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Cancel the previous timer if value changes before delay expires.
    // This is the key: only the LAST keystroke after a pause fires.
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
};

export default useDebounce;