import type { ImplementationPlan, RoadmapItem } from "@/types/api";

function ItemCard({ item }: { item: RoadmapItem }) {
  return (
    <div className="rounded-md border border-ink-200 bg-white p-3 text-sm">
      <div className="text-xs font-semibold uppercase tracking-wide text-brand-600">{item.workstream}</div>
      <div className="mt-1 font-medium text-ink-900">{item.action}</div>
      <div className="mt-2 space-y-1 text-xs text-ink-500">
        <div>Owner: {item.owner}</div>
        {item.dependency && <div>Dependency: {item.dependency}</div>}
        <div>KPI: {item.kpi}</div>
        <div>Outcome: {item.expected_outcome}</div>
        {item.linked_to && <div className="italic">Responds to: {item.linked_to}</div>}
      </div>
    </div>
  );
}

function Column({ title, items }: { title: string; items: RoadmapItem[] }) {
  return (
    <div className="flex-1 space-y-2">
      <h4 className="text-sm font-semibold text-ink-800">{title}</h4>
      {items.length === 0 && <p className="text-xs text-ink-400">No items.</p>}
      {items.map((item, i) => (
        <ItemCard key={i} item={item} />
      ))}
    </div>
  );
}

export function RoadmapTab({ plan }: { plan: ImplementationPlan }) {
  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-ink-600">90-Day Action Plan</h3>
        <div className="mt-3 flex flex-col gap-4 sm:flex-row">
          <Column title="Days 0–30" items={plan.ninety_day_plan.days_0_30} />
          <Column title="Days 31–60" items={plan.ninety_day_plan.days_31_60} />
          <Column title="Days 61–90" items={plan.ninety_day_plan.days_61_90} />
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-ink-600">12-Month Roadmap</h3>
        <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Column title="Quarter 1" items={plan.twelve_month_roadmap.quarter_1} />
          <Column title="Quarter 2" items={plan.twelve_month_roadmap.quarter_2} />
          <Column title="Quarter 3" items={plan.twelve_month_roadmap.quarter_3} />
          <Column title="Quarter 4" items={plan.twelve_month_roadmap.quarter_4} />
        </div>
      </div>

      <div className="rounded-lg border border-ink-200 p-4">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-600">Governance Model</h3>
        <p className="mt-2 text-sm text-ink-700">{plan.governance_model}</p>
      </div>
    </div>
  );
}
