import { Lightbulb, Thermometer, Clock, Leaf } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../ui";
import { recommendationsData, type RecommendationData } from "../../data/dashboardData";
import { cn } from "../../lib/utils";

const iconMap = {
  lightbulb: Lightbulb,
  thermometer: Thermometer,
  clock: Clock,
  leaf: Leaf,
};

interface RecommendationItemProps {
  recommendation: RecommendationData;
  index: number;
}

function RecommendationItem({ recommendation, index }: RecommendationItemProps) {
  const Icon = iconMap[recommendation.icon];

  return (
    <div
      className={cn(
        "flex items-start gap-3 p-3 rounded-xl",
        "bg-secondary-100 dark:bg-secondary-700/50",
        "transition-all duration-200 hover:bg-secondary-200 dark:hover:bg-secondary-700",
        "animate-slide-up"
      )}
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <div className="flex-shrink-0 p-2 rounded-lg bg-primary-200/50 dark:bg-primary-700/30">
        <Icon className="h-4 w-4 text-primary-600 dark:text-primary-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-secondary-900 dark:text-white truncate">
          {recommendation.title}
        </p>
        <p className="text-xs text-secondary-500 dark:text-secondary-400 line-clamp-2">
          {recommendation.description}
        </p>
      </div>
    </div>
  );
}

interface RecommendationsCardProps {
  className?: string;
}

export function RecommendationsCard({ className }: RecommendationsCardProps) {
  return (
    <Card className={cn("col-span-12 md:col-span-6 lg:col-span-3", className)}>
      <CardHeader>
        <CardTitle>Recommendations</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {recommendationsData.map((rec, index) => (
          <RecommendationItem key={rec.id} recommendation={rec} index={index} />
        ))}
      </CardContent>
    </Card>
  );
}

export default RecommendationsCard;

