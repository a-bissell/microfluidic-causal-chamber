import { cn } from "../../lib/utils";

interface MiniBarChartProps {
  bars: number[];
  className?: string;
  barClassName?: string;
  variant?: "default" | "mint";
  maxHeight?: number;
}

export function MiniBarChart({
  bars,
  className,
  barClassName,
  variant = "default",
  maxHeight = 48,
}: MiniBarChartProps) {
  const maxValue = Math.max(...bars);

  return (
    <div
      className={cn(
        "flex items-end gap-0.5",
        className
      )}
      style={{ height: maxHeight }}
    >
      {bars.map((value, index) => {
        const height = (value / maxValue) * 100;
        return (
          <div
            key={index}
            className={cn(
              "flex-1 rounded-t-sm transition-all duration-300",
              "animate-bar-grow",
              variant === "default" && "bg-white/80 dark:bg-white/80",
              variant === "mint" && "bg-secondary-900/70",
              barClassName
            )}
            style={{
              height: `${height}%`,
              animationDelay: `${index * 30}ms`,
            }}
          />
        );
      })}
    </div>
  );
}

export default MiniBarChart;

