import React from 'react';

interface ProgressProps {
  value: number;
  className?: string;
}

export const Progress: React.FC<ProgressProps> = ({ value, className = '' }) => {
  const clampedValue = Math.min(100, Math.max(0, value));
  
  return (
    <div className={`relative w-full bg-gray-200 rounded-full overflow-hidden ${className}`}>
      <div
        className="h-full bg-blue-500 transition-all duration-300 ease-out"
        style={{ width: `${clampedValue}%` }}
      />
    </div>
  );
};