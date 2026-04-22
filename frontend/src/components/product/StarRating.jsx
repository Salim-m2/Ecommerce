/**
 * StarRating component.
 *
 * Renders filled, half, and empty stars based on a 0-5 float rating.
 * Optionally shows the review count next to the stars.
 *
 * Usage:
 *   <StarRating rating={4.3} count={87} />
 *   <StarRating rating={5} size="lg" />
 */
import { Star, StarHalf } from 'lucide-react';

const sizeMap = {
  sm: { star: 12, text: 'text-xs',  gap: 'gap-0.5' },
  md: { star: 16, text: 'text-sm',  gap: 'gap-1'   },
  lg: { star: 20, text: 'text-base', gap: 'gap-1'  },
};

const StarRating = ({ rating = 0, count, size = 'md' }) => {
  const { star: starSize, text: textSize, gap } = sizeMap[size] || sizeMap.md;

  // Build an array of 5 star descriptors: 'full', 'half', or 'empty'
  const stars = Array.from({ length: 5 }, (_, i) => {
    const position = i + 1;
    if (rating >= position) return 'full';
    if (rating >= position - 0.5) return 'half';
    return 'empty';
  });

  return (
    <div className={`flex items-center ${gap}`}>
      {stars.map((type, index) => (
        <span key={index} className="relative inline-flex">
          {type === 'full' && (
            <Star
              size={starSize}
              className="fill-amber-400 text-amber-400"
            />
          )}
          {type === 'half' && (
            <span className="relative inline-flex">
              {/* Empty star base */}
              <Star size={starSize} className="text-gray-300" />
              {/* Half-filled star overlaid, clipped to left half */}
              <span
                className="absolute inset-0 overflow-hidden"
                style={{ width: '50%' }}
              >
                <Star size={starSize} className="fill-amber-400 text-amber-400" />
              </span>
            </span>
          )}
          {type === 'empty' && (
            <Star size={starSize} className="text-gray-300" />
          )}
        </span>
      ))}

      {count !== undefined && count !== null && (
        <span className={`${textSize} text-gray-500 ml-1`}>
          ({count.toLocaleString()})
        </span>
      )}
    </div>
  );
};

export default StarRating;