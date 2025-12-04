import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import Login from './components/Login';
import Register from './components/Register';
import Home from './components/Home';
import Level2 from './components/Level2';
import Level3 from './components/Level3';
import ProductDetail from './components/ProductDetail';
import ProtectedRoute from './components/ProtectedRoute';

const App = () => {
  return (
    <Router>
      <AuthProvider>
        <div className="min-h-screen bg-gradient-to-b from-blue-50 to-gray-100" style={{ direction: 'rtl' }}>
          <Navbar />
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Home />
                </ProtectedRoute>
              }
            />
            <Route
              path="/category/:level1Id"
              element={
                <ProtectedRoute>
                  <Level2 />
                </ProtectedRoute>
              }
            />
            <Route
              path="/category/:level1Id/sub/:level2Id"
              element={
                <ProtectedRoute>
                  <Level3 />
                </ProtectedRoute>
              }
            />
            <Route
              path="/product/:productId"
              element={
                <ProtectedRoute>
                  <ProductDetail />
                </ProtectedRoute>
              }
            />

            {/* Fallback route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </AuthProvider>
    </Router>
  );
};

export default App;
