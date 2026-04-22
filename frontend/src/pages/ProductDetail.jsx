/**
 * ProductDetail page.
 *
 * Layout (desktop): image gallery left column, product info right column.
 * Below: Description / Reviews / Shipping tabs.
 * Bottom: Related products carousel.
 *
 * Key logic:
 * - Variant selection updates the displayed price and stock status
 * - Out-of-stock variants are visually disabled and unselectable
 * - Add to Cart is disabled until a variant is selected
 */
import { useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Swiper, SwiperSlide } from 'swiper/react';
import { Navigation, Thumbs, FreeMode } from 'swiper/modules';
import 'swiper/css';
import 'swiper/css/navigation';
import 'swiper/css/thumbs';
import 'swiper/css/free-mode';
import toast from 'react-hot-toast';
import { Heart, ShoppingCart, ChevronLeft, Minus, Plus } from 'lucide-react';

import { useProduct, useProducts } from '../hooks/useProducts';
import ProductGrid from '../components/product/ProductGrid';
import StarRating from '../components/product/StarRating';
import { formatPrice, buildCloudinaryUrl } from '../utils/formatters';

// ── Tab content components ─────────────────────────────────────────────────

const DescriptionTab = ({ description }) => (
  <div className="prose prose-sm max-w-none text-gray-700 leading-relaxed">
    {description
      ? description.split('\n').map((para, i) => <p key={i}>{para}</p>)
      : <p className="text-gray-400 italic">No description provided.</p>
    }
  </div>
);

const ReviewsTab = () => (
  <div className="text-center py-10 text-gray-400">
    <p className="text-4xl mb-2">⭐</p>
    <p className="font-medium text-gray-600">Reviews coming in Week 7</p>
    <p className="text-sm mt-1">Verified purchase reviews will appear here.</p>
  </div>
);

const ShippingTab = () => (
  <div className="space-y-4 text-sm text-gray-700">
    <div>
      <h4 className="font-semibold text-gray-900 mb-1">Standard Shipping</h4>
      <p>Delivered in 5–7 business days. Free on orders over $50.</p>
    </div>
    <div>
      <h4 className="font-semibold text-gray-900 mb-1">Express Shipping</h4>
      <p>Delivered in 1–2 business days. $15 flat rate.</p>
    </div>
    <div>
      <h4 className="font-semibold text-gray-900 mb-1">Returns</h4>
      <p>
        Free returns within 30 days of delivery. Items must be unused and
        in original packaging.
      </p>
    </div>
  </div>
);

// ── Skeleton loader ────────────────────────────────────────────────────────

const DetailSkeleton = () => (
  <div className="max-w-screen-xl mx-auto px-4 py-8 animate-pulse">
    <div className="flex flex-col lg:flex-row gap-10">
      <div className="lg:w-1/2 aspect-square bg-gray-200 rounded-2xl" />
      <div className="lg:w-1/2 space-y-4">
        <div className="h-4 bg-gray-200 rounded w-1/4" />
        <div className="h-8 bg-gray-200 rounded w-3/4" />
        <div className="h-4 bg-gray-200 rounded w-1/3" />
        <div className="h-10 bg-gray-200 rounded w-1/3" />
        <div className="h-24 bg-gray-200 rounded" />
        <div className="h-12 bg-gray-200 rounded" />
      </div>
    </div>
  </div>
);

// ── Main component ─────────────────────────────────────────────────────────

const TABS = ['Description', 'Reviews', 'Shipping'];

const ProductDetail = () => {
  const { slug } = useParams();
  const { data: product, isLoading, isError } = useProduct(slug);

  // Swiper thumbs instance — needed for the thumbnail sync
  const [thumbsSwiper, setThumbsSwiper] = useState(null);

  // Which variant the user has selected (null = none selected yet)
  const [selectedVariant, setSelectedVariant] = useState(null);

  // Quantity input
  const [quantity, setQuantity] = useState(1);

  // Active tab
  const [activeTab, setActiveTab] = useState('Description');

  // Related products — same category, excluding this product
  const { data: relatedData } = useProducts(
    product
      ? { category: product.category_id, page_size: 5 }
      : {}
  );
  const relatedProducts = useMemo(() => {
    if (!relatedData?.results || !product) return [];
    return relatedData.results.filter(p => p.slug !== slug).slice(0, 4);
  }, [relatedData, product, slug]);

  // ── Derived state ──────────────────────────────────────────────────────

  // Unique colors and sizes across all variants
  const colors = useMemo(() => {
    if (!product?.variants) return [];
    return [...new Set(product.variants.map(v => v.color).filter(Boolean))];
  }, [product]);

  const sizes = useMemo(() => {
    if (!product?.variants) return [];
    return [...new Set(product.variants.map(v => v.size).filter(Boolean))];
  }, [product]);

  // Currently selected color and size (derived from selectedVariant)
  const [selectedColor, setSelectedColor] = useState(null);
  const [selectedSize,  setSelectedSize]  = useState(null);

  // Find the matching variant whenever color or size changes
  const matchedVariant = useMemo(() => {
    if (!product?.variants) return null;
    return product.variants.find(v => {
      const colorMatch = !colors.length || v.color === selectedColor;
      const sizeMatch  = !sizes.length  || v.size  === selectedSize;
      return colorMatch && sizeMatch;
    }) || null;
  }, [product, selectedColor, selectedSize, colors, sizes]);

  // The variant to use for price / stock display
  const activeVariant = matchedVariant || selectedVariant;

  // Price to display
  const displayPrice = activeVariant?.price ?? product?.base_price;

  // Stock of the selected variant
  const variantStock = activeVariant?.stock ?? 0;

  // Whether to show "Add to Cart" as enabled
  const hasVariantSelected = colors.length === 0 && sizes.length === 0
    ? true // no variants — always enabled
    : !!matchedVariant;
  const canAddToCart = hasVariantSelected && variantStock > 0;

  // ── Handlers ──────────────────────────────────────────────────────────

  const handleColorSelect = (color) => {
    setSelectedColor(color);
    setQuantity(1);
  };

  const handleSizeSelect = (size) => {
    setSelectedSize(size);
    setQuantity(1);
  };

  const handleAddToCart = () => {
    toast('Cart coming in Week 5! 🛒', { icon: '🛒' });
  };

  const handleAddToWishlist = () => {
    toast('Wishlist coming in Week 7! ❤️', { icon: '❤️' });
  };

  // ── Render ─────────────────────────────────────────────────────────────

  if (isLoading) return <DetailSkeleton />;

  if (isError || !product) {
    return (
      <div className="max-w-screen-xl mx-auto px-4 py-16 text-center">
        <p className="text-5xl mb-4">🔍</p>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Product not found</h2>
        <p className="text-gray-500 mb-6">
          This product may have been removed or the link is incorrect.
        </p>
        <Link
          to="/products"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-colors"
        >
          <ChevronLeft size={16} /> Back to Products
        </Link>
      </div>
    );
  }

  const images = product.images?.length > 0
    ? product.images
    : [''];  // fallback so gallery renders even with no images

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-screen-xl mx-auto px-4 py-8">

        {/* Breadcrumb */}
        <nav className="text-sm text-gray-400 mb-6 flex items-center gap-1.5">
          <Link to="/" className="hover:text-indigo-600 transition-colors">Home</Link>
          <span>/</span>
          <Link to="/products" className="hover:text-indigo-600 transition-colors">Products</Link>
          <span>/</span>
          <span className="text-gray-600 font-medium truncate">{product.name}</span>
        </nav>

        {/* ── Main two-column layout ─────────────────────────────────────── */}
        <div className="flex flex-col lg:flex-row gap-10 mb-12">

          {/* Left: Image gallery */}
          <div className="lg:w-1/2">
            {images.length > 1 ? (
              <>
                {/* Main swiper */}
                <Swiper
                  modules={[Navigation, Thumbs]}
                  navigation
                  thumbs={{ swiper: thumbsSwiper && !thumbsSwiper.destroyed ? thumbsSwiper : null }}
                  className="rounded-2xl overflow-hidden border border-gray-100 mb-3"
                  style={{ aspectRatio: '1 / 1' }}
                >
                  {images.map((img, i) => (
                    <SwiperSlide key={i}>
                      <img
                        src={buildCloudinaryUrl(img, 800)}
                        alt={`${product.name} — view ${i + 1}`}
                        className="w-full h-full object-cover"
                      />
                    </SwiperSlide>
                  ))}
                </Swiper>

                {/* Thumbnail row */}
                <Swiper
                  modules={[FreeMode, Thumbs]}
                  onSwiper={setThumbsSwiper}
                  spaceBetween={8}
                  slidesPerView={4}
                  freeMode
                  watchSlidesProgress
                  className="thumbnail-swiper"
                >
                  {images.map((img, i) => (
                    <SwiperSlide key={i}>
                      <div className="aspect-square rounded-xl overflow-hidden border-2 border-transparent cursor-pointer hover:border-indigo-400 transition-colors swiper-slide-thumb-active:border-indigo-500">
                        <img
                          src={buildCloudinaryUrl(img, 150)}
                          alt={`Thumbnail ${i + 1}`}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    </SwiperSlide>
                  ))}
                </Swiper>
              </>
            ) : (
              // Single image — no Swiper needed
              <div className="rounded-2xl overflow-hidden border border-gray-100 aspect-square bg-gray-50">
                {images[0] ? (
                  <img
                    src={buildCloudinaryUrl(images[0], 800)}
                    alt={product.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-300">
                    <span className="text-8xl">📦</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right: Product info */}
          <div className="lg:w-1/2 flex flex-col">

            {/* Brand */}
            {product.brand && (
              <p className="text-sm font-semibold text-indigo-500 uppercase tracking-wider mb-1">
                {product.brand}
              </p>
            )}

            {/* Name */}
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 leading-tight mb-2">
              {product.name}
            </h1>

            {/* Rating */}
            <div className="flex items-center gap-2 mb-4">
              <StarRating rating={product.avg_rating} count={product.review_count} size="md" />
            </div>

            {/* Price */}
            <p className="text-3xl font-bold text-gray-900 mb-5">
              {formatPrice(displayPrice)}
              {activeVariant && activeVariant.price !== product.base_price && (
                <span className="text-sm font-normal text-gray-400 ml-2">
                  (variant price)
                </span>
              )}
            </p>

            {/* Color selector */}
            {colors.length > 0 && (
              <div className="mb-4">
                <p className="text-sm font-semibold text-gray-700 mb-2">
                  Color
                  {selectedColor && (
                    <span className="font-normal text-gray-500 ml-1.5">— {selectedColor}</span>
                  )}
                </p>
                <div className="flex flex-wrap gap-2">
                  {colors.map(color => {
                    const hasStock = product.variants.some(
                      v => v.color === color && v.stock > 0
                    );
                    return (
                      <button
                        key={color}
                        onClick={() => hasStock && handleColorSelect(color)}
                        className={`px-3 py-1.5 rounded-lg border text-sm font-medium transition-all
                          ${selectedColor === color
                            ? 'border-indigo-600 bg-indigo-50 text-indigo-700 ring-2 ring-indigo-300'
                            : hasStock
                              ? 'border-gray-200 text-gray-700 hover:border-gray-400'
                              : 'border-gray-100 text-gray-300 cursor-not-allowed line-through'
                          }`}
                      >
                        {color}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Size selector */}
            {sizes.length > 0 && (
              <div className="mb-4">
                <p className="text-sm font-semibold text-gray-700 mb-2">
                  Size
                  {selectedSize && (
                    <span className="font-normal text-gray-500 ml-1.5">— {selectedSize}</span>
                  )}
                </p>
                <div className="flex flex-wrap gap-2">
                  {sizes.map(size => {
                    const variant = product.variants.find(
                      v => v.size === size &&
                        (!selectedColor || v.color === selectedColor)
                    );
                    const hasStock = variant ? variant.stock > 0 : false;
                    return (
                      <button
                        key={size}
                        onClick={() => hasStock && handleSizeSelect(size)}
                        className={`w-12 h-10 rounded-lg border text-sm font-medium transition-all
                          ${selectedSize === size
                            ? 'border-indigo-600 bg-indigo-50 text-indigo-700 ring-2 ring-indigo-300'
                            : hasStock
                              ? 'border-gray-200 text-gray-700 hover:border-gray-400'
                              : 'border-gray-100 text-gray-200 cursor-not-allowed line-through'
                          }`}
                      >
                        {size}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Stock message */}
            {hasVariantSelected && variantStock === 0 && (
              <p className="text-sm text-red-500 font-medium mb-3">
                This variant is out of stock.
              </p>
            )}
            {hasVariantSelected && variantStock > 0 && variantStock <= 5 && (
              <p className="text-sm text-amber-600 font-medium mb-3">
                Only {variantStock} left in stock!
              </p>
            )}

            {/* Quantity + CTA buttons */}
            <div className="flex items-center gap-3 mt-2">
              {/* Quantity control */}
              <div className="flex items-center border border-gray-200 rounded-xl overflow-hidden">
                <button
                  onClick={() => setQuantity(q => Math.max(1, q - 1))}
                  className="px-3 py-2.5 text-gray-600 hover:bg-gray-50 transition-colors"
                  disabled={quantity <= 1}
                >
                  <Minus size={14} />
                </button>
                <span className="w-10 text-center text-sm font-semibold text-gray-900">
                  {quantity}
                </span>
                <button
                  onClick={() => setQuantity(q => Math.min(variantStock, q + 1))}
                  className="px-3 py-2.5 text-gray-600 hover:bg-gray-50 transition-colors"
                  disabled={!canAddToCart || quantity >= variantStock}
                >
                  <Plus size={14} />
                </button>
              </div>

              {/* Add to Cart */}
              <button
                onClick={handleAddToCart}
                disabled={!canAddToCart}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-5 rounded-xl font-semibold text-sm transition-all
                  ${canAddToCart
                    ? 'bg-indigo-600 text-white hover:bg-indigo-700 active:scale-95 shadow-sm'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  }`}
              >
                <ShoppingCart size={16} />
                {!hasVariantSelected
                  ? 'Select options'
                  : variantStock === 0
                    ? 'Out of Stock'
                    : 'Add to Cart'
                }
              </button>

              {/* Wishlist */}
              <button
                onClick={handleAddToWishlist}
                className="p-2.5 border border-gray-200 rounded-xl text-gray-500 hover:text-red-500 hover:border-red-200 transition-colors"
                aria-label="Add to wishlist"
              >
                <Heart size={18} />
              </button>
            </div>

            {/* Tags */}
            {product.tags?.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-5 pt-5 border-t border-gray-100">
                {product.tags.map(tag => (
                  <span
                    key={tag}
                    className="px-2.5 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}

          </div>
        </div>

        {/* ── Tabs ───────────────────────────────────────────────────────── */}
        <div className="border-t border-gray-100 mb-10">

          {/* Tab nav */}
          <div className="flex gap-0 border-b border-gray-100">
            {TABS.map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors
                  ${activeTab === tab
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-800'
                  }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="py-6">
            {activeTab === 'Description' && <DescriptionTab description={product.description} />}
            {activeTab === 'Reviews'     && <ReviewsTab />}
            {activeTab === 'Shipping'    && <ShippingTab />}
          </div>

        </div>

        {/* ── Related products ────────────────────────────────────────────── */}
        {relatedProducts.length > 0 && (
          <div className="border-t border-gray-100 pt-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">You may also like</h2>
            <ProductGrid
              products={relatedProducts}
              isLoading={false}
              skeletonCount={4}
            />
          </div>
        )}

      </div>
    </div>
  );
};

export default ProductDetail;