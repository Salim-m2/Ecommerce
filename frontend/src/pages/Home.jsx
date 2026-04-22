/**
 * Home page.
 *
 * Sections:
 *   1. Hero banner
 *   2. Category grid (from useCategories)
 *   3. Featured Products (highest rated)
 *   4. New Arrivals (most recent)
 */
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { useCategories, useProducts } from '../hooks/useProducts';
import ProductGrid from '../components/product/ProductGrid';

// ── Category card ──────────────────────────────────────────────────────────

const CategoryCard = ({ category }) => (
  <Link
    to={`/products?category=${category.slug}`}
    className="group relative flex flex-col items-center justify-end rounded-2xl overflow-hidden aspect-square bg-gradient-to-br from-indigo-50 to-indigo-100 border border-indigo-100 hover:shadow-lg transition-all duration-200 hover:-translate-y-1"
  >
    {/* Category image */}
    {category.image_url && (
      <img
        src={category.image_url}
        alt={category.name}
        loading="lazy"
        className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-80 transition-opacity duration-300"
      />
    )}

    {/* Name overlay */}
    <div className="relative z-10 w-full bg-gradient-to-t from-black/60 to-transparent px-3 pb-3 pt-6">
      <p className="text-white font-bold text-sm text-center">{category.name}</p>
    </div>
  </Link>
);

// ── Section header ─────────────────────────────────────────────────────────

const SectionHeader = ({ title, linkTo, linkLabel = 'View all' }) => (
  <div className="flex items-center justify-between mb-5">
    <h2 className="text-xl lg:text-2xl font-bold text-gray-900">{title}</h2>
    {linkTo && (
      <Link
        to={linkTo}
        className="flex items-center gap-1 text-sm text-indigo-600 font-medium hover:text-indigo-800 transition-colors"
      >
        {linkLabel} <ArrowRight size={14} />
      </Link>
    )}
  </div>
);

// ── Main component ─────────────────────────────────────────────────────────

const Home = () => {
  const { data: categories = [], isLoading: catsLoading } = useCategories();

  const { data: featuredData, isLoading: featuredLoading } = useProducts({
    sort: 'rating',
    page_size: 8,
  });

  const { data: newData, isLoading: newLoading } = useProducts({
    sort: 'newest',
    page_size: 8,
  });

  const featuredProducts = featuredData?.results || [];
  const newProducts      = newData?.results      || [];

  // Only show top-level categories on the home page
  const topLevelCategories = categories.filter(c => !c.parent_id);

  return (
    <div className="min-h-screen bg-gray-50">

      {/* ── Hero ───────────────────────────────────────────────────────── */}
      <section className="relative bg-gradient-to-br from-indigo-900 via-indigo-700 to-purple-800 text-white overflow-hidden">
        {/* Decorative circles */}
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-white/5 rounded-full" />
        <div className="absolute -bottom-16 -left-16 w-64 h-64 bg-white/5 rounded-full" />

        <div className="relative max-w-screen-xl mx-auto px-4 py-20 lg:py-28 flex flex-col items-center text-center">
          <span className="inline-block bg-white/15 backdrop-blur-sm text-white text-xs font-semibold px-3 py-1 rounded-full mb-4 border border-white/20">
            New arrivals every week
          </span>
          <h1 className="text-4xl lg:text-6xl font-extrabold leading-tight mb-4 max-w-3xl">
            Discover Products You'll{' '}
            <span className="text-amber-300">Love</span>
          </h1>
          <p className="text-indigo-200 text-lg max-w-xl mb-8">
            Shop the latest trends in electronics, footwear, clothing, and more.
            Free shipping on orders over $50.
          </p>
          <Link
            to="/products"
            className="inline-flex items-center gap-2 bg-white text-indigo-700 font-bold px-7 py-3.5 rounded-2xl hover:bg-indigo-50 transition-colors shadow-lg text-base"
          >
            Shop Now <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      <div className="max-w-screen-xl mx-auto px-4 py-10 space-y-14">

        {/* ── Categories ─────────────────────────────────────────────────── */}
        {!catsLoading && topLevelCategories.length > 0 && (
          <section>
            <SectionHeader
              title="Shop by Category"
              linkTo="/products"
              linkLabel="All products"
            />
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {topLevelCategories.map(cat => (
                <CategoryCard key={cat.slug} category={cat} />
              ))}
            </div>
          </section>
        )}

        {/* ── Featured products ───────────────────────────────────────────── */}
        <section>
          <SectionHeader
            title="Featured Products"
            linkTo="/products?sort=rating"
            linkLabel="See all"
          />
          <ProductGrid
            products={featuredProducts}
            isLoading={featuredLoading}
            skeletonCount={8}
          />
        </section>

        {/* ── New arrivals ────────────────────────────────────────────────── */}
        <section>
          <SectionHeader
            title="New Arrivals"
            linkTo="/products?sort=newest"
            linkLabel="See all"
          />
          <ProductGrid
            products={newProducts}
            isLoading={newLoading}
            skeletonCount={8}
          />
        </section>

        {/* ── Footer strip ────────────────────────────────────────────────── */}
        <section className="border-t border-gray-200 pt-8 pb-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-center text-sm text-gray-500">
            <div>
              <p className="text-2xl mb-1">🚚</p>
              <p className="font-semibold text-gray-700">Free Shipping</p>
              <p>On orders over $50</p>
            </div>
            <div>
              <p className="text-2xl mb-1">🔄</p>
              <p className="font-semibold text-gray-700">30-Day Returns</p>
              <p>Hassle-free returns</p>
            </div>
            <div>
              <p className="text-2xl mb-1">🔒</p>
              <p className="font-semibold text-gray-700">Secure Checkout</p>
              <p>SSL encrypted payments</p>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
};

export default Home;