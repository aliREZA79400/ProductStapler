import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { productAPI } from '../services/api';

const ProductDetail = () => {
  const { productId } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadProduct();
  }, [productId]);

  const loadProduct = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await productAPI.getProductById(productId);
      setProduct(response.data);
    } catch (err) {
      if (err.response?.status === 404) {
        setError('Product not found.');
      } else {
        setError('Failed to load product details. Please try again.');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <button
          onClick={() => navigate(-1)}
          className="mb-4 text-blue-500 hover:text-blue-600"
        >
          ← Back
        </button>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    );
  }

  const renderValue = (value) => {
    if (typeof value === 'object' && value !== null) {
      return (
        <pre className="bg-gray-100 p-2 rounded text-sm overflow-x-auto">
          {JSON.stringify(value, null, 2)}
        </pre>
      );
    }
    return <span className="text-gray-800">{String(value)}</span>;
  };

  // Extract images if they exist
  const productImages = product?.images && Array.isArray(product.images) ? product.images : [];
  // Filter out images from the regular fields display
  const displayFields = product ? Object.entries(product).filter(([key]) => key !== 'images') : [];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <button
        onClick={() => navigate(-1)}
        className="mb-6 text-blue-500 hover:text-blue-600 font-medium"
      >
        ← Back
      </button>

      <div className="bg-white rounded-lg shadow-md p-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Product Details</h1>
        
        {/* Product Images Gallery */}
        {productImages.length > 0 && (
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-700 mb-3">Images</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {productImages.map((imageUrl, idx) => (
                <div key={idx} className="aspect-square overflow-hidden rounded-lg bg-gray-100">
                  <img
                    src={imageUrl}
                    alt={`Product image ${idx + 1}`}
                    className="w-full h-full object-cover hover:scale-105 transition-transform duration-200"
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Other Product Information */}
        <div className="space-y-4">
          {displayFields.map(([key, value]) => (
            <div key={key} className="border-b border-gray-200 pb-4 last:border-b-0">
              <div className="font-semibold text-gray-700 mb-1 capitalize">
                {key.replace(/_/g, ' ')}:
              </div>
              <div className="ml-4">
                {renderValue(value)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ProductDetail;
