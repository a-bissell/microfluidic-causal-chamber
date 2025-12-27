import { type ReactNode } from "react";
import { cn } from "../../lib/utils";

interface CardProps {
  children: ReactNode;
  className?: string;
  variant?: "default" | "mint";
}

export function Card({ children, className, variant = "default" }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-card p-card transition-all duration-200",
        variant === "default" && [
          "bg-white dark:bg-secondary-800",
          "text-secondary-900 dark:text-white",
        ],
        variant === "mint" && [
          "bg-primary-200",
          "text-secondary-900",
          "shadow-card-mint",
        ],
        className
      )}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  children: ReactNode;
  className?: string;
}

export function CardHeader({ children, className }: CardHeaderProps) {
  return (
    <div className={cn("mb-4", className)}>
      {children}
    </div>
  );
}

interface CardTitleProps {
  children: ReactNode;
  className?: string;
  variant?: "default" | "mint";
}

export function CardTitle({ children, className, variant = "default" }: CardTitleProps) {
  return (
    <h3
      className={cn(
        "text-title font-medium",
        variant === "default" && "text-secondary-900 dark:text-white",
        variant === "mint" && "text-secondary-900",
        className
      )}
    >
      {children}
    </h3>
  );
}

interface CardContentProps {
  children: ReactNode;
  className?: string;
}

export function CardContent({ children, className }: CardContentProps) {
  return (
    <div className={cn(className)}>
      {children}
    </div>
  );
}

export default Card;

