/**
 * ProductGrid component.
 *
 * Renders a responsive grid of ProductCards.
 * While loading, renders animated skeleton cards so the layout doesn't jump.
 *
 * Props:
 *   products      - array of product objects (from ProductListSerializer)
 *   isLoading     - bool — show skeletons when true
 *   skeletonCount - number of skeleton cards to show (default 12)
 */
import ProductCard from './ProductCard';

/**
 * Single skeleton card — mimics the ProductCard layout with a pulse animation.
 * Using explicit height values keeps the skeleton the same size as real cards.
 */
const SkeletonCard = () => (
  <div className="flex flex-col bg-white rounded-xl overflow-hidden border border-gray-100 shadow-sm animate-pulse">
    {/* Image placeholder */}
    <div className="aspect-square bg-gray-200" />
    {/* Text placeholders */}
    <div className="p-3 flex flex-col gap-2">
      <div className="h-3 bg-gray-200 rounded w-1/3" />
      <div className="h-4 bg-gray-200 rounded w-full" />
      <div className="h-4 bg-gray-200 rounded w-3/4" />
      <div className="h-3 bg-gray-200 rounded w-1/2 mt-1" />
      <div className="h-5 bg-gray-200 rounded w-1/3 mt-1" />
    </div>
  </div>
);

const ProductGrid = ({ products = [], isLoading = false, skeletonCount = 12 }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {isLoading
        ? Array.from({ length: skeletonCount }, (_, i) => (
            <SkeletonCard key={i} />
          ))
        : products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
    </div>
  );
};

export default ProductGrid;