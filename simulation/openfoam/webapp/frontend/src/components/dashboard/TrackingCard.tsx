import { Sun, TrendingUp } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../ui";
import { trackingData } from "../../data/dashboardData";
import { cn } from "../../lib/utils";

interface TrackingCardProps {
  className?: string;
}

export function TrackingCard({ className }: TrackingCardProps) {
  return (
    <Card 
      variant="mint" 
      className={cn("col-span-12 md:col-span-6 lg:col-span-3", className)}
    >
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle variant="mint">Tracking</CardTitle>
        <Sun className="h-5 w-5 text-secondary-900/70" />
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {/* Hero stat */}
        <div className="animate-fade-in">
          <p className="stat-hero text-secondary-900">
            {trackingData.value}
            <span className="text-2xl font-normal ml-1">
              {trackingData.unit}
            </span>
          </p>
          <p className="text-sm text-secondary-900/70 mt-1">
            {trackingData.label}
          </p>
        </div>

        {/* Trend indicator */}
        <div className="flex items-center gap-2 text-secondary-900/70">
          <TrendingUp className="h-4 w-4" />
          <span className="text-xs font-medium">{trackingData.trend}</span>
        </div>
      </CardContent>
    </Card>
  );
}

export default TrackingCard;

