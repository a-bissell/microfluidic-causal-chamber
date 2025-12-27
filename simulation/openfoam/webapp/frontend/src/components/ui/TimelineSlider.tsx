import { cn } from "../../lib/utils";
import type { TimelineNode } from "../../data/dashboardData";

interface TimelineSliderProps {
  nodes: TimelineNode[];
  className?: string;
  variant?: "default" | "mint";
}

export function TimelineSlider({
  nodes,
  className,
  variant = "default",
}: TimelineSliderProps) {
  return (
    <div className={cn("w-full", className)}>
      {/* Timeline track */}
      <div className="relative">
        {/* Background track */}
        <div
          className={cn(
            "h-1 w-full rounded-full",
            variant === "default" && "bg-secondary-700",
            variant === "mint" && "bg-secondary-900/20"
          )}
        />
        
        {/* Active portion - calculate based on active nodes */}
        <div
          className={cn(
            "absolute top-0 left-0 h-1 rounded-full transition-all duration-300",
            variant === "default" && "bg-primary-400",
            variant === "mint" && "bg-secondary-900"
          )}
          style={{
            width: `${(nodes.filter(n => n.isActive).length / nodes.length) * 100}%`,
            marginLeft: `${(nodes.findIndex(n => n.isActive) / nodes.length) * 100}%`,
          }}
        />

        {/* Nodes */}
        <div className="absolute top-0 left-0 right-0 flex justify-between -translate-y-1/2">
          {nodes.map((node, index) => (
            <div key={index} className="flex flex-col items-center">
              <div
                className={cn(
                  "h-3 w-3 rounded-full border-2 transition-all duration-200",
                  node.isActive
                    ? variant === "default"
                      ? "bg-primary-400 border-primary-400"
                      : "bg-secondary-900 border-secondary-900"
                    : variant === "default"
                      ? "bg-secondary-800 border-secondary-600"
                      : "bg-primary-200 border-secondary-900/30"
                )}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Time labels */}
      <div className="flex justify-between mt-3">
        {nodes.map((node, index) => (
          <span
            key={index}
            className={cn(
              "text-xs font-medium",
              node.isActive
                ? variant === "default"
                  ? "text-white"
                  : "text-secondary-900"
                : variant === "default"
                  ? "text-secondary-500"
                  : "text-secondary-900/50"
            )}
          >
            {node.time}
          </span>
        ))}
      </div>
    </div>
  );
}

export default TimelineSlider;

