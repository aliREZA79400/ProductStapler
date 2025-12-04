import React, { useEffect, useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { productAPI } from '../services/api';
import ProductCard from './ProductCard';

const Level2 = () => {
  const { level1Id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sampleSize, setSampleSize] = useState(5);

  useEffect(() => {
    loadProducts();
  }, [level1Id, sampleSize]);

  const loadProducts = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await productAPI.getLevel2Products(parseInt(level1Id), sampleSize);
      setData(response.data);
    } catch (err) {
      if (err.response?.status === 404) {
        setError('No products found for this category.');
      } else {
        setError('Failed to load products. Please try again.');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="text-xl text-gray-600">⏳ درحال بارگذاری...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <button
          onClick={() => navigate(-1)}
          className="mb-4 text-blue-500 hover:text-blue-600"
        >
          ← بازگشت
        </button>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          ❌ {error}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <button
        onClick={() => navigate(-1)}
        className="mb-4 text-blue-500 hover:text-blue-600 font-medium"
      >
        ← بازگشت به دسته‌بندی‌ها
      </button>

      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          🏷️ دسته {level1Id} - زیردسته‌ها
        </h1>
        <p className="text-gray-600">{data?.message}</p>
        
        <div className="mt-4 flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">
            تعداد محصولات در هر زیردسته:
          </label>
          <select
            value={sampleSize}
            onChange={(e) => setSampleSize(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={1}>۱</option>
            <option value={3}>۳</option>
            <option value={5}>۵</option>
            <option value={10}>۱۰</option>
          </select>
        </div>
      </div>

      {data?.results && Object.entries(data.results).map(([levelId, levelData]) => (
        <div key={levelId} className="mb-8 bg-gradient-to-br from-gray-50 to-blue-50 rounded-lg p-6 border-r-4 border-blue-500">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-semibold text-gray-800">
              🔖 زیردسته {levelData.level2_id}
            </h2>
            <Link
              to={`/category/${level1Id}/sub/${levelData.level2_id}`}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md transition duration-200"
            >
              ← مشاهده زیردسته‌های بیشتر
            </Link>
          </div>
          
          <p className="text-sm text-gray-600 mb-4">
            📊 نمایش {levelData.sample_size} محصول
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {levelData.products?.map((product, idx) => (
              <ProductCard key={idx} product={product} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default Level2;
