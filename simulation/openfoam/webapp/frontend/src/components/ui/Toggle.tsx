import { cn } from "../../lib/utils";

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  className?: string;
  disabled?: boolean;
  label?: string;
}

export function Toggle({
  checked,
  onChange,
  className,
  disabled = false,
  label,
}: ToggleProps) {
  return (
    <label
      className={cn(
        "inline-flex items-center gap-3 cursor-pointer",
        disabled && "cursor-not-allowed opacity-50",
        className
      )}
    >
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange(!checked)}
        className={cn(
          "relative inline-flex h-6 w-11 shrink-0 items-center rounded-full",
          "transition-colors duration-200 ease-in-out",
          "focus-visible:outline-none focus-visible:ring-2",
          "focus-visible:ring-primary-400 focus-visible:ring-offset-2",
          "dark:focus-visible:ring-offset-secondary-900",
          checked
            ? "bg-primary-500"
            : "bg-secondary-200 dark:bg-secondary-700"
        )}
      >
        <span
          className={cn(
            "pointer-events-none block h-5 w-5 rounded-full bg-white shadow-sm",
            "ring-0 transition-transform duration-200 ease-in-out",
            checked ? "translate-x-5" : "translate-x-0.5"
          )}
        />
      </button>
      {label && (
        <span className="text-sm font-medium text-secondary-700 dark:text-secondary-300">
          {label}
        </span>
      )}
    </label>
  );
}

export default Toggle;

