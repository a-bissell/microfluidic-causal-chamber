/**
 * Sample data for the Mevolut Dashboard
 * All data is separated from components for maintainability
 */

export interface ConsumptionData {
  label: string;
  value: number;
  unit: string;
  bars: number[];
}

export interface RecommendationData {
  id: string;
  title: string;
  description: string;
  icon: "lightbulb" | "thermometer" | "clock" | "leaf";
}

export interface WeeklyReportData {
  day: string;
  value: number;
  isSelected?: boolean;
}

export interface TimelineNode {
  time: string;
  label: string;
  isActive?: boolean;
}

// Total Energy Consumption - Mini bar charts data
export const consumptionData: ConsumptionData[] = [
  {
    label: "Lighting",
    value: 87,
    unit: "kWh",
    bars: [35, 60, 45, 80, 55, 90, 70, 65, 85, 50, 75, 40],
  },
  {
    label: "Refrigerator",
    value: 134,
    unit: "kWh",
    bars: [70, 65, 75, 60, 72, 68, 74, 70, 66, 78, 72, 69],
  },
  {
    label: "Air Conditioner",
    value: 203,
    unit: "kWh",
    bars: [20, 35, 60, 85, 95, 100, 95, 85, 60, 40, 25, 15],
  },
];

// Green Connections data
export const greenConnectionsData = {
  percentage: 83,
  isEnabled: true,
};

// Recommendations data
export const recommendationsData: RecommendationData[] = [
  {
    id: "1",
    title: "Optimize AC Schedule",
    description: "Shift cooling to off-peak hours to save 15% on energy costs",
    icon: "thermometer",
  },
  {
    id: "2",
    title: "Smart Lighting",
    description: "Enable motion sensors to reduce lighting consumption by 20%",
    icon: "lightbulb",
  },
  {
    id: "3",
    title: "Peak Hour Alert",
    description: "Avoid high consumption between 2-5 PM for better rates",
    icon: "clock",
  },
];

// Tracking card data
export const trackingData = {
  value: 5.7,
  unit: "kWh",
  label: "Solar energy tomorrow",
  trend: "+12% from yesterday",
};

// Detailed Report - Weekly bar chart data
export const weeklyReportData: WeeklyReportData[] = [
  { day: "Mon", value: 45 },
  { day: "Tue", value: 62 },
  { day: "Wed", value: 38, isSelected: true },
  { day: "Thu", value: 55 },
  { day: "Fri", value: 78 },
  { day: "Sat", value: 42 },
  { day: "Sun", value: 35 },
];

// Green Energy Usage data
export const greenEnergyData = {
  percentage: 47,
  timeline: [
    { time: "11 AM", label: "Start", isActive: false },
    { time: "12 PM", label: "", isActive: false },
    { time: "1 PM", label: "Peak", isActive: true },
    { time: "2 PM", label: "", isActive: true },
    { time: "3 PM", label: "", isActive: false },
    { time: "4 PM", label: "End", isActive: false },
  ] as TimelineNode[],
};

// Navigation items
export const navItems = [
  { label: "Dashboard", href: "#", isActive: true },
  { label: "My apartments", href: "#", isActive: false },
  { label: "Reporting", href: "#", isActive: false },
  { label: "Settings", href: "#", isActive: false },
];

// User profile data
export const userData = {
  name: "Alex M.",
  avatar: null, // Using initials instead
  initials: "AM",
};

