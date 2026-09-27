import type { Level } from "@/types/api";
import { levelBadgeClasses } from "@/lib/levels";

export function LevelBadge({ level }: { level: Level }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${levelBadgeClasses(level)}`}>
      {level}
    </span>
  );
}

export function Badge({ children, tone = "neutral" }: { children: React.ReactNode; tone?: "neutral" | "brand" | "demo" }) {
  const toneClasses = {
    neutral: "bg-ink-100 text-ink-700 border-ink-200",
    brand: "bg-brand-100 text-brand-700 border-brand-100",
    demo: "bg-purple-100 text-purple-700 border-purple-200",
  }[tone];
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${toneClasses}`}>
      {children}
    </span>
  );
}
