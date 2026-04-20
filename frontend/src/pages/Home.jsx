// src/pages/Home.jsx
// Full home page built in Week 3

const Home = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">

      {/* Hero */}
      <div className="mb-6 inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-sm font-medium">
        <span className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-pulse" />
        Now live — shop the latest drops
      </div>

      <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight mb-6">
        <span className="bg-gradient-to-r from-violet-400 via-purple-400 to-teal-400 bg-clip-text text-transparent">
          ShopZetu
        </span>
        <br />
        <span className="text-white">Built for Kenya.</span>
      </h1>

      <p className="text-slate-400 text-lg max-w-xl mx-auto mb-10">
        A production-grade e-commerce platform. Fast, secure, and built from scratch.
      </p>

      <div className="flex items-center justify-center gap-4 flex-wrap">
        
        <a  href="/products"
          className="px-6 py-3 bg-violet-600 hover:bg-violet-700 text-white rounded-lg font-medium transition-colors"
        >
          Browse Products
        </a>
        <a
          href="/register"
          className="px-6 py-3 border border-slate-700 hover:border-slate-600 text-slate-300 hover:text-white rounded-lg font-medium transition-colors"
        >
          Create Account
        </a>
      </div>

      {/* Week indicator */}
      <p className="mt-16 text-xs text-slate-700">
        Week 1 — Auth foundation complete. Product catalog coming in Week 3.
      </p>

    </div>
  )
}

export default Home