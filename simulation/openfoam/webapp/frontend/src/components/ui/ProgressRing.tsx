import { cn } from "../../lib/utils";

interface ProgressRingProps {
  percentage: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
  variant?: "default" | "mint";
}

export function ProgressRing({
  percentage,
  size = 80,
  strokeWidth = 6,
  className,
  variant = "default",
}: ProgressRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <svg
        width={size}
        height={size}
        className="transform -rotate-90"
      >
        {/* Background ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          className={cn(
            variant === "default" && "stroke-secondary-700 dark:stroke-secondary-600",
            variant === "mint" && "stroke-secondary-900/20"
          )}
        />
        {/* Progress ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={cn(
            "transition-all duration-500 ease-out",
            variant === "default" && "stroke-primary-400",
            variant === "mint" && "stroke-secondary-900"
          )}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span
          className={cn(
            "text-lg font-semibold",
            variant === "default" && "text-white",
            variant === "mint" && "text-secondary-900"
          )}
        >
          {percentage}%
        </span>
      </div>
    </div>
  );
}

export default ProgressRing;

