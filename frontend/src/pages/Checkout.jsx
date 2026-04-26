import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import { CheckCircle2, ChevronRight, ChevronLeft, Truck, Zap } from 'lucide-react';

import useCart from '../hooks/useCart';
import { useDispatch } from 'react-redux';
import { fetchCart } from '../store/cartSlice';
import orderAPI from '../api/orderAPI';
import { formatPrice } from '../utils/formatters';

// ── Zod schema for Step 1 ─────────────────────────────────────────────────────
const addressSchema = z.object({
  full_name:   z.string().min(2,  'Full name is required'),
  phone:       z.string().min(9,  'Valid phone number required'),
  street:      z.string().min(3,  'Street address is required'),
  city:        z.string().min(2,  'City is required'),
  country:     z.string().min(1,  'Country is required').default('Kenya'),
  postal_code: z.string().optional(),
});

// ── Shipping method config ────────────────────────────────────────────────────
const SHIPPING_METHODS = [
  {
    id:          'standard',
    label:       'Standard Shipping',
    description: 'Delivered to your door',
    eta:         '5–7 business days',
    cost:        5.00,
    icon:        Truck,
  },
  {
    id:          'express',
    label:       'Express Shipping',
    description: 'Priority handling and delivery',
    eta:         '1–2 business days',
    cost:        15.00,
    icon:        Zap,
  },
];

// ── Step indicator ────────────────────────────────────────────────────────────
const STEPS = [
  { number: 1, label: 'Address'  },
  { number: 2, label: 'Shipping' },
  { number: 3, label: 'Payment'  },
];

function StepIndicator({ currentStep }) {
  return (
    <div className="flex items-center justify-center mb-10">
      {STEPS.map((step, idx) => (
        <div key={step.number} className="flex items-center">
          {/* Circle */}
          <div className="flex flex-col items-center">
            <div
              className={`
                w-9 h-9 rounded-full flex items-center justify-center
                text-sm font-bold transition-colors
                ${currentStep > step.number
                  ? 'bg-violet-600 text-white'
                  : currentStep === step.number
                    ? 'bg-violet-600 text-white ring-4 ring-violet-600/30'
                    : 'bg-slate-700 text-slate-400'}
              `}
            >
              {currentStep > step.number
                ? <CheckCircle2 size={16} />
                : step.number}
            </div>
            <span
              className={`mt-1.5 text-xs font-medium ${
                currentStep >= step.number ? 'text-violet-400' : 'text-slate-500'
              }`}
            >
              {step.label}
            </span>
          </div>

          {/* Connector line between circles */}
          {idx < STEPS.length - 1 && (
            <div
              className={`w-20 h-0.5 mx-2 mb-5 transition-colors ${
                currentStep > step.number ? 'bg-violet-600' : 'bg-slate-700'
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );
}

// ── Order summary sidebar (shown on Step 2) ───────────────────────────────────
function OrderSummary({ items, subtotal, shippingCost }) {
  const total = subtotal + shippingCost;

  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-6">
      <h3 className="text-base font-semibold text-white mb-4">Order Summary</h3>

      <ul className="space-y-3 mb-4 max-h-56 overflow-y-auto pr-1">
        {items.map((item, idx) => (
          <li key={idx} className="flex items-center gap-3">
            {item.image_url ? (
              <img
                src={item.image_url}
                alt={item.product_name}
                className="w-10 h-10 rounded-lg object-cover flex-shrink-0 bg-slate-700"
              />
            ) : (
              <div className="w-10 h-10 rounded-lg bg-slate-700 flex-shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm text-slate-200 truncate">{item.product_name}</p>
              {(item.color || item.size) && (
                <p className="text-xs text-slate-500">
                  {[item.color, item.size].filter(Boolean).join(' / ')}
                </p>
              )}
            </div>
            <div className="text-sm text-slate-300 flex-shrink-0">
              {formatPrice(item.price_at_add * item.quantity)}
            </div>
          </li>
        ))}
      </ul>

      <div className="border-t border-slate-700 pt-4 space-y-2 text-sm">
        <div className="flex justify-between text-slate-400">
          <span>Subtotal</span>
          <span>{formatPrice(subtotal)}</span>
        </div>
        <div className="flex justify-between text-slate-400">
          <span>Shipping</span>
          <span>{formatPrice(shippingCost)}</span>
        </div>
        <div className="flex justify-between text-white font-semibold text-base pt-2 border-t border-slate-700">
          <span>Total</span>
          <span>{formatPrice(total)}</span>
        </div>
      </div>
    </div>
  );
}

// ── Main Checkout component ───────────────────────────────────────────────────
export default function Checkout() {
  const navigate  = useNavigate();
  const dispatch  = useDispatch();
  const { cart, items, subtotal } = useCart();

  // Ephemeral checkout state — lives only for this page visit
  const [step,           setStep]           = useState(1);
  const [addressData,    setAddressData]    = useState(null);
  const [shippingMethod, setShippingMethod] = useState('standard');
  const [isSubmitting,   setIsSubmitting]   = useState(false);

  const selectedMethod = SHIPPING_METHODS.find(m => m.id === shippingMethod);

  // ── react-hook-form for Step 1 ──────────────────────────────────────────
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver:      zodResolver(addressSchema),
    defaultValues: { country: 'Kenya' },
  });

  // ── Step 1 submit ────────────────────────────────────────────────────────
  const onAddressSubmit = (data) => {
    setAddressData(data);
    setStep(2);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // ── Step 2 submit — create the order, then advance to Step 3 ─────────────
  const onShippingSubmit = async () => {
    setIsSubmitting(true);
    try {
      const order = await orderAPI.createOrder({
        shipping_address: addressData,
        shipping_method:  shippingMethod,
        notes:            '',
      });

      // Refresh the cart count in Redux — cart was cleared server-side
      dispatch(fetchCart());

      // Navigate straight to payment page with the created order id
      // Step 3 (payment) is on its own page built in Day 5
      navigate(`/checkout/payment/${order.id}`, { state: { order } });

    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.items?.[0] ||
        'Could not create your order. Please try again.';
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── Redirect if cart is empty ─────────────────────────────────────────────
  if (!items || items.length === 0) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center px-4 text-center">
        <p className="text-slate-400 text-lg mb-4">Your cart is empty.</p>
        <button
          onClick={() => navigate('/products')}
          className="px-6 py-3 bg-violet-600 hover:bg-violet-700 text-white font-semibold rounded-xl transition-colors"
        >
          Browse Products
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 py-10 px-4">
      <div className="max-w-4xl mx-auto">

        {/* Page title */}
        <h1 className="text-2xl font-bold text-white text-center mb-2">Checkout</h1>
        <p className="text-slate-400 text-center text-sm mb-8">
          {items.length} item{items.length !== 1 ? 's' : ''} · {formatPrice(subtotal)} subtotal
        </p>

        {/* Step indicator */}
        <StepIndicator currentStep={step} />

        {/* ── STEP 1: Shipping Address ──────────────────────────────────── */}
        {step === 1 && (
          <div className="max-w-lg mx-auto">
            <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-6 md:p-8">
              <h2 className="text-lg font-semibold text-white mb-6">Shipping Address</h2>

              <form onSubmit={handleSubmit(onAddressSubmit)} className="space-y-4">

                {/* Full name */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Full Name <span className="text-red-400">*</span>
                  </label>
                  <input
                    {...register('full_name')}
                    placeholder="John Kamau"
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3
                               text-white placeholder-slate-500 text-sm
                               focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500
                               transition-colors"
                  />
                  {errors.full_name && (
                    <p className="mt-1.5 text-xs text-red-400">{errors.full_name.message}</p>
                  )}
                </div>

                {/* Phone */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Phone Number <span className="text-red-400">*</span>
                  </label>
                  <input
                    {...register('phone')}
                    placeholder="+254712345678"
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3
                               text-white placeholder-slate-500 text-sm
                               focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500
                               transition-colors"
                  />
                  {errors.phone && (
                    <p className="mt-1.5 text-xs text-red-400">{errors.phone.message}</p>
                  )}
                </div>

                {/* Street */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Street Address <span className="text-red-400">*</span>
                  </label>
                  <input
                    {...register('street')}
                    placeholder="123 Kenyatta Avenue"
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3
                               text-white placeholder-slate-500 text-sm
                               focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500
                               transition-colors"
                  />
                  {errors.street && (
                    <p className="mt-1.5 text-xs text-red-400">{errors.street.message}</p>
                  )}
                </div>

                {/* City + Country row */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">
                      City <span className="text-red-400">*</span>
                    </label>
                    <input
                      {...register('city')}
                      placeholder="Nairobi"
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3
                                 text-white placeholder-slate-500 text-sm
                                 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500
                                 transition-colors"
                    />
                    {errors.city && (
                      <p className="mt-1.5 text-xs text-red-400">{errors.city.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">
                      Country <span className="text-red-400">*</span>
                    </label>
                    <input
                      {...register('country')}
                      placeholder="Kenya"
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3
                                 text-white placeholder-slate-500 text-sm
                                 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500
                                 transition-colors"
                    />
                    {errors.country && (
                      <p className="mt-1.5 text-xs text-red-400">{errors.country.message}</p>
                    )}
                  </div>
                </div>

                {/* Postal code (optional) */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Postal Code <span className="text-slate-500 text-xs">(optional)</span>
                  </label>
                  <input
                    {...register('postal_code')}
                    placeholder="00100"
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3
                               text-white placeholder-slate-500 text-sm
                               focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500
                               transition-colors"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full mt-2 py-3.5 bg-violet-600 hover:bg-violet-700
                             text-white font-semibold rounded-xl
                             flex items-center justify-center gap-2
                             transition-colors"
                >
                  Next: Shipping Method
                  <ChevronRight size={16} />
                </button>
              </form>
            </div>
          </div>
        )}

        {/* ── STEP 2: Shipping Method ───────────────────────────────────── */}
        {step === 2 && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Left: method selection */}
            <div className="lg:col-span-2">
              <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-6 md:p-8">
                <h2 className="text-lg font-semibold text-white mb-6">Shipping Method</h2>

                <div className="space-y-4">
                  {SHIPPING_METHODS.map((method) => {
                    const Icon     = method.icon;
                    const selected = shippingMethod === method.id;

                    return (
                      <button
                        key={method.id}
                        type="button"
                        onClick={() => setShippingMethod(method.id)}
                        className={`
                          w-full flex items-center gap-4 p-5 rounded-xl border-2
                          text-left transition-all
                          ${selected
                            ? 'border-violet-500 bg-violet-500/10'
                            : 'border-slate-700 bg-slate-900/40 hover:border-slate-600'}
                        `}
                      >
                        {/* Icon */}
                        <div
                          className={`
                            w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0
                            ${selected ? 'bg-violet-600' : 'bg-slate-700'}
                          `}
                        >
                          <Icon size={18} className="text-white" />
                        </div>

                        {/* Details */}
                        <div className="flex-1">
                          <p className={`font-semibold text-sm ${selected ? 'text-white' : 'text-slate-300'}`}>
                            {method.label}
                          </p>
                          <p className="text-xs text-slate-500 mt-0.5">
                            {method.description} · {method.eta}
                          </p>
                        </div>

                        {/* Price + check */}
                        <div className="flex items-center gap-3 flex-shrink-0">
                          <span className={`font-semibold text-sm ${selected ? 'text-violet-400' : 'text-slate-300'}`}>
                            {formatPrice(method.cost)}
                          </span>
                          <div
                            className={`
                              w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0
                              ${selected ? 'border-violet-500 bg-violet-500' : 'border-slate-600'}
                            `}
                          >
                            {selected && <CheckCircle2 size={12} className="text-white" />}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>

                {/* Navigation buttons */}
                <div className="flex gap-3 mt-8">
                  <button
                    type="button"
                    onClick={() => { setStep(1); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                    className="flex-1 py-3.5 border border-slate-700 hover:border-slate-500
                               text-slate-300 font-semibold rounded-xl
                               flex items-center justify-center gap-2
                               transition-colors"
                  >
                    <ChevronLeft size={16} />
                    Back
                  </button>

                  <button
                    type="button"
                    onClick={onShippingSubmit}
                    disabled={isSubmitting}
                    className="flex-1 py-3.5 bg-violet-600 hover:bg-violet-700
                               disabled:opacity-60 disabled:cursor-not-allowed
                               text-white font-semibold rounded-xl
                               flex items-center justify-center gap-2
                               transition-colors"
                  >
                    {isSubmitting ? (
                      <>
                        <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Creating order…
                      </>
                    ) : (
                      <>
                        Next: Payment
                        <ChevronRight size={16} />
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Right: order summary */}
            <div className="lg:col-span-1">
              <OrderSummary
                items        = {items}
                subtotal     = {subtotal}
                shippingCost = {selectedMethod?.cost ?? 5.00}
              />
            </div>
          </div>
        )}

      </div>
    </div>
  );
}