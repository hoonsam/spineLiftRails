import React, { useState, useEffect } from 'react';
import { Range, getTrackBackground } from 'react-range';
import type { ParameterConfig } from './types';

interface ParameterSliderProps {
  config: ParameterConfig;
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}

export const ParameterSlider: React.FC<ParameterSliderProps> = ({
  config,
  value,
  onChange,
  disabled = false
}) => {
  const [localValue, setLocalValue] = useState(value);
  
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const percentage = ((localValue - config.min) / (config.max - config.min)) * 100;
  const isModified = localValue !== config.defaultValue;

  return (
    <div className="parameter-slider mb-4">
      <div className="flex justify-between items-center mb-2">
        <label className="text-sm font-medium text-gray-200">
          {config.label}
          {config.unit && <span className="text-gray-400 ml-1">({config.unit})</span>}
        </label>
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={localValue}
            onChange={(e) => {
              const newValue = parseFloat(e.target.value);
              if (!isNaN(newValue)) {
                const clampedValue = Math.min(Math.max(newValue, config.min), config.max);
                setLocalValue(clampedValue);
                onChange(clampedValue);
              }
            }}
            min={config.min}
            max={config.max}
            step={config.step}
            className="w-20 px-2 py-1 text-sm bg-gray-700 text-white border border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={disabled}
          />
          {isModified && (
            <button
              onClick={() => {
                setLocalValue(config.defaultValue);
                onChange(config.defaultValue);
              }}
              className="text-xs text-blue-500 hover:text-blue-700"
              title="Reset to default"
              disabled={disabled}
            >
              Reset
            </button>
          )}
        </div>
      </div>
      
      <Range
        values={[localValue]}
        step={config.step}
        min={config.min}
        max={config.max}
        onChange={(values) => {
          setLocalValue(values[0]);
          onChange(values[0]);
        }}
        disabled={disabled}
        renderTrack={({ props, children }) => (
          <div
            onMouseDown={props.onMouseDown}
            onTouchStart={props.onTouchStart}
            style={{
              ...props.style,
              height: '36px',
              display: 'flex',
              width: '100%'
            }}
          >
            <div
              ref={props.ref}
              style={{
                height: '4px',
                width: '100%',
                borderRadius: '2px',
                background: getTrackBackground({
                  values: [localValue],
                  colors: disabled ? ['#d1d5db', '#e5e7eb'] : ['#3b82f6', '#e5e7eb'],
                  min: config.min,
                  max: config.max
                }),
                alignSelf: 'center'
              }}
            >
              {children}
            </div>
          </div>
        )}
        renderThumb={({ props }) => (
          <div
            {...props}
            style={{
              ...props.style,
              height: '16px',
              width: '16px',
              borderRadius: '50%',
              backgroundColor: disabled ? '#9ca3af' : '#3b82f6',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
              cursor: disabled ? 'not-allowed' : 'grab'
            }}
          />
        )}
      />
      
      {config.description && (
        <p className="text-xs text-gray-500 mt-1">{config.description}</p>
      )}
      
      <div className="flex justify-between text-xs text-gray-400 mt-1">
        <span>{config.min}</span>
        <span className="text-blue-600 font-medium">{percentage.toFixed(0)}%</span>
        <span>{config.max}</span>
      </div>
    </div>
  );
};