import React from 'react';

// Stapler Logo Component
const StaplerLogo = ({ size = 40, className = '' }) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Stapler Head (Top Part) */}
      <path
        d="M 20 30 L 80 15 L 85 35 L 25 45 Z"
        fill="#1e40af"
        stroke="#1e3a8a"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      
      {/* Stapler Head Detail */}
      <ellipse cx="52" cy="30" rx="20" ry="8" fill="none" stroke="#3b82f6" strokeWidth="1" opacity="0.6" />
      
      {/* Stapler Body (Main Part) */}
      <rect
        x="15"
        y="40"
        width="70"
        height="35"
        rx="4"
        fill="#3b82f6"
        stroke="#1e3a8a"
        strokeWidth="1.5"
      />
      
      {/* Stapler Handle */}
      <path
        d="M 30 40 L 28 70 L 35 72 L 37 40 Z"
        fill="#1e40af"
        stroke="#1e3a8a"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      
      {/* Handle Grip Lines */}
      <line x1="30" y1="50" x2="32" y2="60" stroke="#fbbf24" strokeWidth="1" opacity="0.7" />
      <line x1="31" y1="55" x2="34" y2="65" stroke="#fbbf24" strokeWidth="1" opacity="0.7" />
      <line x1="32" y1="60" x2="35" y2="70" stroke="#fbbf24" strokeWidth="1" opacity="0.7" />
      
      {/* Metal Staple Inside */}
      <path
        d="M 45 55 Q 50 45 55 55"
        fill="none"
        stroke="#fbbf24"
        strokeWidth="2"
        strokeLinecap="round"
      />
      
      {/* Bottom Plate */}
      <rect
        x="18"
        y="72"
        width="64"
        height="6"
        rx="2"
        fill="#1e40af"
        stroke="#1e3a8a"
        strokeWidth="1.5"
      />
      
      {/* Bottom Plate Shine */}
      <rect
        x="20"
        y="73"
        width="60"
        height="2"
        rx="1"
        fill="#60a5fa"
        opacity="0.6"
      />
      
      {/* Gold Accent Strip */}
      <rect
        x="15"
        y="38"
        width="70"
        height="2"
        fill="#fbbf24"
        opacity="0.8"
      />
    </svg>
  );
};

const PersianDecoration = ({ position = 'top' }) => {
  // Persian cultural patterns with stapler logos
  const patterns = [
    '🔗',
    '📎',
    '📌',
    '🧷',
  ];

  if (position === 'top') {
    return (
      <div className="flex justify-center items-center gap-4 mb-6">
        <StaplerLogo size={45} className="animate-pulse" style={{ animationDelay: '0s' }} />
        {patterns.map((pattern, idx) => (
          <span key={idx} className="text-3xl animate-pulse" style={{ animationDelay: `${idx * 0.1}s` }}>
            {pattern}
          </span>
        ))}
        <StaplerLogo size={45} className="animate-pulse" style={{ animationDelay: '0.2s' }} />
      </div>
    );
  }

  if (position === 'bottom') {
    return (
      <div className="flex justify-center items-center gap-3 mt-6">
        <StaplerLogo size={35} className="animate-bounce" style={{ animationDelay: '0s' }} />
        {patterns.slice(0, 3).map((pattern, idx) => (
          <span key={idx} className="text-2xl animate-bounce" style={{ animationDelay: `${idx * 0.1}s` }}>
            {pattern}
          </span>
        ))}
        <StaplerLogo size={35} className="animate-bounce" style={{ animationDelay: '0.15s' }} />
      </div>
    );
  }

  if (position === 'side') {
    return (
      <div className="fixed right-4 top-1/2 transform -translate-y-1/2 opacity-20 pointer-events-none hidden lg:flex flex-col gap-6">
        <StaplerLogo size={50} className="animate-pulse" style={{ animationDelay: '0s' }} />
        {patterns.map((pattern, idx) => (
          <span key={idx} className="text-4xl animate-pulse" style={{ animationDelay: `${idx * 0.2}s` }}>
            {pattern}
          </span>
        ))}
        <StaplerLogo size={50} className="animate-pulse" style={{ animationDelay: '0.4s' }} />
      </div>
    );
  }

  return null;
};

export default PersianDecoration;
