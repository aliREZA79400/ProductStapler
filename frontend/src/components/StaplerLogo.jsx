import React from 'react';

/**
 * StaplerLogo Component
 * A custom SVG stapler logo for the Mangane project
 * Features Persian-inspired design with blue and gold colors
 */
const StaplerLogo = ({
  size = 40,
  className = '',
  animate = false,
  color = '#3b82f6',
  accentColor = '#fbbf24',
}) => {
  const animationClass = animate
    ? 'hover:scale-110 transition-transform duration-300 cursor-pointer'
    : '';

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      xmlns="http://www.w3.org/2000/svg"
      className={`${className} ${animationClass}`}
      style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))' }}
    >
      {/* Stapler Head (Top Part) */}
      <path
        d="M 20 30 L 80 15 L 85 35 L 25 45 Z"
        fill={color}
        stroke="#1e3a8a"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />

      {/* Stapler Head Detail */}
      <ellipse cx="52" cy="30" rx="20" ry="8" fill="none" stroke="#60a5fa" strokeWidth="1" opacity="0.6" />

      {/* Stapler Body (Main Part) */}
      <rect
        x="15"
        y="40"
        width="70"
        height="35"
        rx="4"
        fill={color}
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
      <line x1="30" y1="50" x2="32" y2="60" stroke={accentColor} strokeWidth="1" opacity="0.7" />
      <line x1="31" y1="55" x2="34" y2="65" stroke={accentColor} strokeWidth="1" opacity="0.7" />
      <line x1="32" y1="60" x2="35" y2="70" stroke={accentColor} strokeWidth="1" opacity="0.7" />

      {/* Metal Staple Inside */}
      <path
        d="M 45 55 Q 50 45 55 55"
        fill="none"
        stroke={accentColor}
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
        fill={accentColor}
        opacity="0.8"
      />
    </svg>
  );
};

export default StaplerLogo;
