import { cn } from "../../lib/utils";
import { TotalConsumptionCard } from "./TotalConsumptionCard";
import { GreenConnectionsCard } from "./GreenConnectionsCard";
import { RecommendationsCard } from "./RecommendationsCard";
import { TrackingCard } from "./TrackingCard";
import { DetailedReportCard } from "./DetailedReportCard";
import { GreenEnergyUsageCard } from "./GreenEnergyUsageCard";

interface DashboardGridProps {
  className?: string;
}

export function DashboardGrid({ className }: DashboardGridProps) {
  return (
    <div className={cn("w-full max-w-dashboard mx-auto px-4 sm:px-6 py-6", className)}>
      {/* Dashboard header */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-secondary-900 dark:text-white">
          Dashboard
        </h1>
        <p className="text-sm text-secondary-500 dark:text-secondary-400 mt-1">
          Monitor your energy consumption and green connections
        </p>
      </div>

      {/* Grid layout */}
      <div className="grid grid-cols-12 gap-4 lg:gap-6">
        {/* Row 1 */}
        <TotalConsumptionCard className="animate-slide-up animate-delay-100" />
        <GreenConnectionsCard className="animate-slide-up animate-delay-200" />
        <RecommendationsCard className="animate-slide-up animate-delay-300" />

        {/* Row 2 */}
        <TrackingCard className="animate-slide-up animate-delay-200" />
        <DetailedReportCard className="animate-slide-up animate-delay-300" />
        <GreenEnergyUsageCard className="animate-slide-up animate-delay-400" />
      </div>
    </div>
  );
}

export default DashboardGrid;

