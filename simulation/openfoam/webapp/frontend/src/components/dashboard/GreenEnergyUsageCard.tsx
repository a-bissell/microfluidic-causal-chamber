import { Zap } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent, TimelineSlider } from "../ui";
import { greenEnergyData } from "../../data/dashboardData";
import { cn } from "../../lib/utils";

interface GreenEnergyUsageCardProps {
  className?: string;
}

export function GreenEnergyUsageCard({ className }: GreenEnergyUsageCardProps) {
  return (
    <Card 
      variant="mint" 
      className={cn("col-span-12 md:col-span-6 lg:col-span-5", className)}
    >
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle variant="mint">Green energy usage</CardTitle>
        <Zap className="h-5 w-5 text-secondary-900/70" />
      </CardHeader>
      <CardContent className="flex flex-col gap-6">
        {/* Hero percentage */}
        <div className="animate-fade-in">
          <p className="stat-hero text-secondary-900">
            {greenEnergyData.percentage}
            <span className="text-2xl font-normal">%</span>
          </p>
          <p className="text-sm text-secondary-900/70 mt-1">
            of total consumption
          </p>
        </div>

        {/* Timeline slider */}
        <div className="pt-4">
          <p className="text-xs font-medium text-secondary-900/70 mb-4 uppercase tracking-wider">
            Peak production hours
          </p>
          <TimelineSlider nodes={greenEnergyData.timeline} variant="mint" />
        </div>
      </CardContent>
    </Card>
  );
}

export default GreenEnergyUsageCard;

