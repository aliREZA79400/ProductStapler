import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';

const ProductCard = ({ product }) => {
  // Get random sample of images (up to 3)
  const sampleImages = useMemo(() => {
    if (!product.images || !Array.isArray(product.images) || product.images.length === 0) {
      return [];
    }
    
    // Shuffle array and take first 3
    const shuffled = [...product.images].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, 3);
  }, [product.images]);

  // Filter out _id and images from display fields
  const displayFields = Object.entries(product).filter(
    ([key]) => !['_id', 'images'].includes(key)
  );

  return (
    <div className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow duration-200 border-r-4 border-blue-400">
      {/* Product Images */}
      {sampleImages.length > 0 && (
        <div className="mb-4 grid grid-cols-3 gap-2">
          {sampleImages.map((imageUrl, idx) => (
            <div key={idx} className="aspect-square overflow-hidden rounded-md bg-gray-100">
              <img
                src={imageUrl}
                alt={`تصویر محصول ${idx + 1}`}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            </div>
          ))}
        </div>
      )}
      
      {/* Product Information */}
      <div className="space-y-2">
        {displayFields.map(([key, value]) => (
          <div key={key} className="text-sm">
            <span className="font-semibold text-gray-700">{key}: </span>
            <span className="text-gray-600">
              {typeof value === 'object' ? JSON.stringify(value) : String(value)}
            </span>
          </div>
        ))}
      </div>
      {product._id && (
        <Link
          to={`/product/${product._id}`}
          className="mt-4 inline-block text-blue-500 hover:text-blue-600 text-sm font-medium"
        >
          ← مشاهده جزئیات
        </Link>
      )}
    </div>
  );
};

export default ProductCard;
