'use client';

import { useState, useCallback } from 'react';

interface SliderControlProps {
  label: string;
  description: string;
  minLabel: string;
  maxLabel: string;
  value: number;
  activeValue?: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}

export default function SliderControl({
  label,
  description,
  minLabel,
  maxLabel,
  value,
  activeValue,
  onChange,
  disabled = false,
}: SliderControlProps) {
  const isPending = activeValue !== undefined && value !== activeValue;

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange(parseInt(e.target.value, 10));
    },
    [onChange]
  );

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-slate-200">{label}</label>
        <div className="flex items-center gap-2">
          {isPending && activeValue !== undefined && (
            <span className="text-xs text-slate-500">
              Active: {activeValue}
            </span>
          )}
          <span
            className={`text-sm font-bold ${
              isPending ? 'text-amber-400' : 'text-white'
            }`}
          >
            {value}
          </span>
        </div>
      </div>

      <p className="text-xs text-slate-400">{description}</p>

      <div className="relative pt-1">
        {/* Background track */}
        <div className="h-2 bg-slate-700 rounded-full" />

        {/* Active value indicator (if different from pending) */}
        {isPending && activeValue !== undefined && (
          <div
            className="absolute top-1 h-2 w-1 bg-green-500 rounded-full opacity-75"
            style={{ left: `calc(${((activeValue - 1) / 9) * 100}% - 2px)` }}
            title={`Active: ${activeValue}`}
          />
        )}

        {/* Slider input */}
        <input
          type="range"
          min={1}
          max={10}
          step={1}
          value={value}
          onChange={handleChange}
          disabled={disabled}
          className={`absolute top-0 w-full h-2 appearance-none bg-transparent cursor-pointer
            [&::-webkit-slider-thumb]:appearance-none
            [&::-webkit-slider-thumb]:w-4
            [&::-webkit-slider-thumb]:h-4
            [&::-webkit-slider-thumb]:rounded-full
            [&::-webkit-slider-thumb]:cursor-pointer
            ${
              isPending
                ? '[&::-webkit-slider-thumb]:bg-amber-400 [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-amber-500'
                : '[&::-webkit-slider-thumb]:bg-green-500 [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-green-400'
            }
            [&::-moz-range-thumb]:w-4
            [&::-moz-range-thumb]:h-4
            [&::-moz-range-thumb]:rounded-full
            [&::-moz-range-thumb]:border-0
            [&::-moz-range-thumb]:cursor-pointer
            ${
              isPending
                ? '[&::-moz-range-thumb]:bg-amber-400'
                : '[&::-moz-range-thumb]:bg-green-500'
            }
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
        />
      </div>

      {/* Scale labels */}
      <div className="flex justify-between text-xs text-slate-500 px-0.5">
        <span>{minLabel}</span>
        <span>Balanced</span>
        <span>{maxLabel}</span>
      </div>
    </div>
  );
}
