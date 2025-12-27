import { Card, CardHeader, CardTitle, CardContent } from "../ui";
import { weeklyReportData } from "../../data/dashboardData";
import { cn } from "../../lib/utils";

interface DetailedReportCardProps {
  className?: string;
}

export function DetailedReportCard({ className }: DetailedReportCardProps) {
  const maxValue = Math.max(...weeklyReportData.map(d => d.value));

  return (
    <Card className={cn("col-span-12 md:col-span-6 lg:col-span-4", className)}>
      <CardHeader>
        <CardTitle>Detailed report</CardTitle>
        <p className="text-xs text-secondary-500 dark:text-secondary-400 mt-1">
          Weekly energy usage
        </p>
      </CardHeader>
      <CardContent>
        {/* Bar chart */}
        <div className="flex items-end justify-between gap-2 h-32">
          {weeklyReportData.map((item, index) => {
            const height = (item.value / maxValue) * 100;
            return (
              <div
                key={item.day}
                className="flex-1 flex flex-col items-center gap-2"
              >
                <div
                  className={cn(
                    "w-full rounded-t-md transition-all duration-300",
                    "animate-bar-grow",
                    item.isSelected
                      ? "bg-primary-400"
                      : "bg-secondary-200 dark:bg-secondary-600"
                  )}
                  style={{
                    height: `${height}%`,
                    animationDelay: `${index * 50}ms`,
                  }}
                />
              </div>
            );
          })}
        </div>

        {/* Day labels */}
        <div className="flex justify-between mt-3">
          {weeklyReportData.map((item) => (
            <span
              key={item.day}
              className={cn(
                "flex-1 text-center text-xs font-medium",
                item.isSelected
                  ? "text-primary-500 dark:text-primary-400"
                  : "text-secondary-500 dark:text-secondary-400"
              )}
            >
              {item.day}
            </span>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default DetailedReportCard;

