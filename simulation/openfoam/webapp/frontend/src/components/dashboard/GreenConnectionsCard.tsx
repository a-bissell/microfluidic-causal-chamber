import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent, Toggle, ProgressRing } from "../ui";
import { greenConnectionsData } from "../../data/dashboardData";
import { cn } from "../../lib/utils";

interface GreenConnectionsCardProps {
  className?: string;
}

export function GreenConnectionsCard({ className }: GreenConnectionsCardProps) {
  const [isEnabled, setIsEnabled] = useState(greenConnectionsData.isEnabled);

  return (
    <Card className={cn("col-span-12 md:col-span-6 lg:col-span-3", className)}>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Green connections</CardTitle>
        <Toggle checked={isEnabled} onChange={setIsEnabled} />
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-4">
        {/* 3D Room Wireframe Placeholder */}
        <div className="relative w-full aspect-square max-w-40 flex items-center justify-center">
          {/* Simplified room wireframe SVG */}
          <svg
            viewBox="0 0 100 100"
            className="w-full h-full text-secondary-400 dark:text-secondary-500"
            fill="none"
            stroke="currentColor"
            strokeWidth="0.5"
          >
            {/* Floor */}
            <polygon points="10,70 50,90 90,70 50,50" className="fill-secondary-100 dark:fill-secondary-700/30" />
            {/* Back wall */}
            <polygon points="10,70 10,30 50,10 50,50" className="fill-secondary-50 dark:fill-secondary-700/20" />
            {/* Side wall */}
            <polygon points="50,10 90,30 90,70 50,50" className="fill-secondary-100 dark:fill-secondary-700/40" />
            {/* Window */}
            <rect x="20" y="35" width="15" height="20" className="fill-primary-200/50 dark:fill-primary-400/20" />
            {/* Furniture outline */}
            <rect x="55" y="55" width="20" height="10" className="fill-secondary-200 dark:fill-secondary-600" />
          </svg>
          
          {/* Glow effect when enabled */}
          {isEnabled && (
            <div className="absolute inset-0 bg-primary-400/10 rounded-full blur-2xl animate-pulse-slow" />
          )}
        </div>

        {/* Progress indicator */}
        <div className="flex items-center gap-4">
          <ProgressRing percentage={greenConnectionsData.percentage} size={64} />
          <div>
            <p className="text-sm font-medium text-secondary-900 dark:text-white">
              Connected devices
            </p>
            <p className="text-xs text-secondary-500 dark:text-secondary-400">
              12 of 14 devices
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default GreenConnectionsCard;

