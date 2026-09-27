import type { Level } from "@/types/api";

export const LEVEL_ORDER: Record<Level, number> = { Low: 0, Medium: 1, High: 2 };

export function levelBadgeClasses(level: Level): string {
  switch (level) {
    case "High":
      return "bg-red-100 text-red-700 border-red-200";
    case "Medium":
      return "bg-amber-100 text-amber-700 border-amber-200";
    case "Low":
      return "bg-emerald-100 text-emerald-700 border-emerald-200";
  }
}

export function riskCellClasses(likelihood: Level, impact: Level): string {
  const score = LEVEL_ORDER[likelihood] + LEVEL_ORDER[impact];
  if (score >= 3) return "bg-red-500/90 text-white";
  if (score >= 1) return "bg-amber-400/90 text-ink-900";
  return "bg-emerald-400/80 text-ink-900";
}

export function confidenceBarWidth(level: Level): string {
  switch (level) {
    case "High":
      return "w-full";
    case "Medium":
      return "w-2/3";
    case "Low":
      return "w-1/3";
  }
}
