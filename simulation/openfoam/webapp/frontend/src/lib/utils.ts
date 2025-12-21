import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatTime(seconds: number): string {
  if (seconds < 0.001) return `${(seconds * 1e6).toFixed(1)} µs`
  if (seconds < 1) return `${(seconds * 1000).toFixed(2)} ms`
  return `${seconds.toFixed(3)} s`
}

export function formatPressure(pascals: number): string {
  if (pascals >= 1000) return `${(pascals / 1000).toFixed(1)} kPa`
  return `${pascals.toFixed(0)} Pa`
}

export function formatScientific(value: number, precision: number = 2): string {
  if (value === 0) return "0"
  const exp = Math.floor(Math.log10(Math.abs(value)))
  const mantissa = value / Math.pow(10, exp)
  return `${mantissa.toFixed(precision)}×10^${exp}`
}