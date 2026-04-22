/**
 * ProductCard component.
 *
 * Renders a single product in a grid. The entire card is a link to the
 * product detail page. Uses lazy loading and explicit dimensions to prevent
 * layout shift (CLS).
 *
 * Props:
 *   product - object from ProductListSerializer:
 *     { id, name, slug, brand, base_price, min_price, thumbnail,
 *       avg_rating, review_count, in_stock, category_id }
 */
import { Link } from 'react-router-dom';
import StarRating from './StarRating';
import { formatPrice, buildCloudinaryUrl, truncateText } from '../../utils/formatters';

const ProductCard = ({ product }) => {
  const {
    name,
    slug,
    brand,
    min_price,
    base_price,
    thumbnail,
    avg_rating,
    review_count,
    in_stock,
  } = product;

  // Use the lower of min_price and base_price for the displayed price.
  // min_price reflects the cheapest variant; base_price is the fallback.
  const displayPrice = min_price ?? base_price;

  // Request a 400px wide, auto-format, auto-quality thumbnail from Cloudinary.
  const imageUrl = thumbnail ? buildCloudinaryUrl(thumbnail, 400) : null;

  return (
    <Link
      to={`/products/${slug}`}
      className="group flex flex-col bg-white rounded-xl overflow-hidden border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200 transition-all duration-200 hover:-translate-y-0.5"
    >
      {/* Image container — fixed aspect ratio prevents layout shift */}
      <div className="relative aspect-square bg-gray-50 overflow-hidden">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={name}
            loading="lazy"
            width={400}
            height={400}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          // Placeholder when no image is available
          <div className="w-full h-full flex items-center justify-center">
            <div className="w-16 h-16 rounded-full bg-gray-200 flex items-center justify-center">
              <span className="text-2xl text-gray-400">📦</span>
            </div>
          </div>
        )}

        {/* Out of Stock badge — overlaid on the image */}
        {!in_stock && (
          <div className="absolute inset-0 bg-white/60 flex items-center justify-center">
            <span className="bg-gray-800 text-white text-xs font-semibold px-3 py-1 rounded-full">
              Out of Stock
            </span>
          </div>
        )}
      </div>

      {/* Card body */}
      <div className="p-3 flex flex-col gap-1 flex-1">
        {/* Brand name */}
        {brand && (
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">
            {brand}
          </p>
        )}

        {/* Product name — 2-line clamp so the grid stays aligned */}
        <h3 className="text-sm font-semibold text-gray-900 leading-snug line-clamp-2 group-hover:text-indigo-600 transition-colors">
          {truncateText(name, 60)}
        </h3>

        {/* Rating row */}
        <div className="mt-auto pt-1">
          <StarRating rating={avg_rating} count={review_count} size="sm" />
        </div>

        {/* Price */}
        <p className="text-base font-bold text-gray-900">
          {formatPrice(displayPrice)}
        </p>
      </div>
    </Link>
  );
};

export default ProductCard;