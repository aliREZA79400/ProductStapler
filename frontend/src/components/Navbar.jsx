import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import StaplerLogo from './StaplerLogo';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg border-b-4 border-amber-500">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-20 relative">
          {/* Left spacer for balance */}
          <div className="flex-1"></div>
          
          {/* Center logo */}
          <Link to="/" className="absolute left-1/2 transform -translate-x-1/2 text-3xl font-bold hover:text-amber-200 transition flex items-center gap-3">
            <StaplerLogo size={40} animate={true} />
            <span>منگنه</span>
            <StaplerLogo size={40} animate={true} />
          </Link>

          {/* Right side - User/Auth buttons */}
          <div className="flex items-center gap-6 flex-1 justify-end">
            {user ? (
              <>
                <span className="text-sm">خوش‌آمدید، {user.username}</span>
                <button
                  onClick={handleLogout}
                  className="bg-blue-800 hover:bg-blue-900 px-4 py-2 rounded-md transition duration-200"
                >
                  خروج
                </button>
              </>
            ) : (
              <div className="flex gap-4">
                <Link
                  to="/login"
                  className="hover:text-amber-200 transition"
                >
                  ورود
                </Link>
                <Link
                  to="/register"
                  className="bg-blue-800 hover:bg-blue-900 px-4 py-2 rounded-md transition duration-200"
                >
                  ثبت‌نام
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
