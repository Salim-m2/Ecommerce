/**
 * Shared formatting utilities used across product components.
 */

/**
 * Format a number as a price string.
 * formatPrice(120)        → '$120.00'
 * formatPrice(9.99, 'GBP') → '£9.99'
 */
export const formatPrice = (amount, currency = 'USD') => {
  if (amount === null || amount === undefined) return '';
  return new Intl.NumberFormat('en-US', {
    style:    'currency',
    currency: currency,
    minimumFractionDigits: 2,
  }).format(amount);
};

/**
 * Format a rating to one decimal place.
 * formatRating(4.333) → '4.3'
 * formatRating(5)     → '5.0'
 */
export const formatRating = (rating) => {
  if (rating === null || rating === undefined) return '0.0';
  return Number(rating).toFixed(1);
};

/**
 * Truncate text to a maximum length, appending '...' if cut.
 * truncateText('Hello World', 8) → 'Hello Wo...'
 */
export const truncateText = (text, maxLength = 100) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

/**
 * Insert Cloudinary transformation parameters into an existing URL.
 *
 * Cloudinary serves transformed images on-the-fly and caches them on its CDN.
 * We use this to request the right size for each context (400px for cards,
 * 800px for detail pages) without uploading separate files.
 *
 * Input:  'https://res.cloudinary.com/cloud/image/upload/v123/ecommerce/img.jpg'
 * Output: 'https://res.cloudinary.com/cloud/image/upload/w_400,f_auto,q_auto/v123/ecommerce/img.jpg'
 *
 * If the URL doesn't look like a Cloudinary upload URL (e.g. the placeholder
 * demo URL from seeding), it's returned unchanged.
 */
export const buildCloudinaryUrl = (cloudinaryUrl, width = 400) => {
  if (!cloudinaryUrl) return '';
  const transformation = `w_${width},f_auto,q_auto`;
  if (cloudinaryUrl.includes('/image/upload/')) {
    return cloudinaryUrl.replace('/image/upload/', `/image/upload/${transformation}/`);
  }
  // Not a Cloudinary URL (placeholder, external URL, etc.) — return as-is
  return cloudinaryUrl;
};