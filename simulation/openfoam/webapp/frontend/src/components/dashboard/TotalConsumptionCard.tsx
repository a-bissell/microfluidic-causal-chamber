import { Card, CardHeader, CardTitle, CardContent, MiniBarChart } from "../ui";
import { consumptionData } from "../../data/dashboardData";
import { cn } from "../../lib/utils";

interface TotalConsumptionCardProps {
  className?: string;
}

export function TotalConsumptionCard({ className }: TotalConsumptionCardProps) {
  return (
    <Card className={cn("col-span-12 md:col-span-6", className)}>
      <CardHeader>
        <CardTitle>Total energy consumption</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4">
          {consumptionData.map((item, index) => (
            <div
              key={item.label}
              className={cn(
                "flex flex-col gap-3 p-4 rounded-xl",
                "bg-secondary-100 dark:bg-secondary-700/50",
                "animate-fade-in"
              )}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <MiniBarChart bars={item.bars} maxHeight={56} />
              <div className="space-y-1">
                <p className="text-2xl font-light text-secondary-900 dark:text-white">
                  {item.value}
                  <span className="text-sm font-normal text-secondary-500 dark:text-secondary-400 ml-1">
                    {item.unit}
                  </span>
                </p>
                <p className="text-xs text-secondary-500 dark:text-secondary-400">
                  {item.label}
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default TotalConsumptionCard;

