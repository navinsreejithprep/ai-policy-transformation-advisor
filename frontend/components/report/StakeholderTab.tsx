import { Fragment } from "react";
import type { Level, Stakeholder, StakeholderMatrix } from "@/types/api";
import { Badge } from "@/components/ui/Badge";

const INFLUENCE_ROWS: Level[] = ["High", "Medium", "Low"];
const INTEREST_COLS: Level[] = ["Low", "Medium", "High"];

function InfluenceInterestMatrix({ stakeholders }: { stakeholders: Stakeholder[] }) {
  return (
    <div className="overflow-x-auto">
      <div className="grid min-w-[560px] grid-cols-[80px_repeat(3,1fr)] gap-1 text-xs">
        <div />
        {INTEREST_COLS.map((c) => (
          <div key={c} className="text-center font-medium text-ink-500">
            Interest: {c}
          </div>
        ))}
        {INFLUENCE_ROWS.map((row) => (
          <Fragment key={row}>
            <div className="flex items-center justify-end pr-2 font-medium text-ink-500">
              Influence: {row}
            </div>
            {INTEREST_COLS.map((col) => {
              const cellStakeholders = stakeholders.filter((s) => s.influence === row && s.interest_level === col);
              const emphasis = row === "High" && col === "High";
              return (
                <div
                  key={`${row}-${col}`}
                  className={`min-h-[92px] rounded-md border p-2 ${
                    emphasis ? "border-brand-300 bg-brand-100/50" : "border-ink-200 bg-ink-50"
                  }`}
                >
                  <div className="flex flex-wrap gap-1">
                    {cellStakeholders.map((s) => (
                      <span
                        key={s.name}
                        title={s.role}
                        className="rounded-full border border-ink-300 bg-white px-2 py-0.5 text-[11px] text-ink-700"
                      >
                        {s.name}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </Fragment>
        ))}
      </div>
      <p className="mt-2 text-xs text-ink-400">
        Top-right (High influence / High interest) stakeholders require the closest engagement.
      </p>
    </div>
  );
}

export function StakeholderTab({ matrix }: { matrix: StakeholderMatrix }) {
  return (
    <div className="space-y-6">
      <InfluenceInterestMatrix stakeholders={matrix.stakeholders} />

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-ink-200 text-left text-xs uppercase tracking-wide text-ink-500">
              <th className="py-2 pr-3">Stakeholder</th>
              <th className="py-2 pr-3">Role</th>
              <th className="py-2 pr-3">Concerns</th>
              <th className="py-2 pr-3">Required Engagement</th>
              <th className="py-2 pr-3">Basis</th>
            </tr>
          </thead>
          <tbody>
            {matrix.stakeholders.map((s, i) => (
              <tr key={i} className="border-b border-ink-100 align-top">
                <td className="py-3 pr-3 font-medium text-ink-900">
                  {s.name}
                  <div className="text-xs font-normal text-ink-400">{s.category}</div>
                </td>
                <td className="py-3 pr-3 text-ink-700">{s.role}</td>
                <td className="py-3 pr-3 text-ink-700">
                  <ul className="list-disc pl-4">
                    {s.likely_concerns.map((c, j) => (
                      <li key={j}>{c}</li>
                    ))}
                  </ul>
                </td>
                <td className="py-3 pr-3 text-ink-700">{s.required_engagement}</td>
                <td className="py-3 pr-3">
                  <Badge tone={s.is_inference ? "neutral" : "brand"}>
                    {s.is_inference ? "INFERENCE" : "EVIDENCED"}
                  </Badge>
                </td>
              </tr>
            ))}
            {matrix.stakeholders.length === 0 && (
              <tr>
                <td colSpan={5} className="py-4 text-center text-ink-400">
                  No stakeholders identified.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
