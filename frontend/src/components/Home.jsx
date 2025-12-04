import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { productAPI } from '../services/api';
import ProductCard from './ProductCard';
import PersianDecoration from './PersianDecoration';

const Home = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sampleSize, setSampleSize] = useState(5);

  useEffect(() => {
    loadProducts();
  }, [sampleSize]);

  const loadProducts = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await productAPI.getLevel1Products(sampleSize);
      setData(response.data);
    } catch (err) {
      setError('Failed to load products. Please try again.');
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
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          ❌ {error}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <PersianDecoration position="top" />
      <div className="mb-6">
        <div className="text-center mb-6">
          <h1 className="text-4xl font-bold text-blue-700 mb-2">منگنه</h1>
          <p className="text-gray-600 text-lg">خوش‌آمدید</p>
        </div>
        <h2 className="text-3xl font-bold text-gray-800 mb-2">دسته‌بندی‌ها</h2>
        
        <div className="mt-4 flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">
            تعداد محصولات در هر دسته:
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
              🏷️ دسته‌بندی {levelData.level1_id}
            </h2>
            <Link
              to={`/category/${levelData.level1_id}`}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md transition duration-200"
            >
              ← مشاهده زیردسته‌ها
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
      <PersianDecoration position="bottom" />
    </div>
  );
};

export default Home;
