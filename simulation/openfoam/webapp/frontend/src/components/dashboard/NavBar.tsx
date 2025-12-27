import { Leaf, User } from "lucide-react";
import { ThemeSwitch } from "../ui";
import { navItems, userData } from "../../data/dashboardData";
import { cn } from "../../lib/utils";

interface NavBarProps {
  className?: string;
}

export function NavBar({ className }: NavBarProps) {
  return (
    <nav
      className={cn(
        "w-full py-4 px-6",
        "bg-white/80 dark:bg-secondary-900/80",
        "backdrop-blur-md",
        "border-b border-secondary-100 dark:border-secondary-800",
        "sticky top-0 z-50",
        className
      )}
    >
      <div className="max-w-dashboard mx-auto flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-primary-200 dark:bg-primary-700">
            <Leaf className="h-5 w-5 text-primary-700 dark:text-primary-200" />
          </div>
          <span className="text-lg font-semibold text-secondary-900 dark:text-white">
            Mevolut
          </span>
        </div>

        {/* Navigation Links */}
        <div className="hidden md:flex items-center gap-8">
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className={cn(
                "nav-link",
                item.isActive && "nav-link-active"
              )}
            >
              {item.label}
            </a>
          ))}
        </div>

        {/* Right section */}
        <div className="flex items-center gap-4">
          {/* Theme switch */}
          <ThemeSwitch />

          {/* User profile */}
          <button
            className={cn(
              "flex items-center gap-2 p-1.5 rounded-full",
              "bg-secondary-100 dark:bg-secondary-800",
              "hover:bg-secondary-200 dark:hover:bg-secondary-700",
              "transition-colors duration-200"
            )}
          >
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-200 dark:bg-primary-700">
              {userData.avatar ? (
                <img
                  src={userData.avatar}
                  alt={userData.name}
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                <User className="h-4 w-4 text-primary-700 dark:text-primary-200" />
              )}
            </div>
            <span className="hidden sm:block text-sm font-medium text-secondary-700 dark:text-secondary-300 pr-2">
              {userData.name}
            </span>
          </button>
        </div>
      </div>
    </nav>
  );
}

export default NavBar;

