import type { ImplementationPlan } from "@/types/api";

export function KpiTab({ plan }: { plan: ImplementationPlan }) {
  if (plan.kpis.length === 0) {
    return <p className="text-sm text-ink-400">No KPIs defined.</p>;
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {plan.kpis.map((kpi, i) => (
        <div key={i} className="rounded-lg border border-ink-200 p-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-brand-600">{kpi.workstream}</div>
          <div className="mt-1 font-medium text-ink-900">{kpi.name}</div>
          <div className="mt-2 text-sm text-ink-600">Target: {kpi.target}</div>
        </div>
      ))}
    </div>
  );
}
