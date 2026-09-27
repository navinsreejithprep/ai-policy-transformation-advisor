import { Fragment } from "react";
import type { Level, RiskRegister } from "@/types/api";
import { LevelBadge } from "@/components/ui/Badge";
import { riskCellClasses } from "@/lib/levels";

const IMPACT_COLS: Level[] = ["Low", "Medium", "High"];
const LIKELIHOOD_ROWS: Level[] = ["High", "Medium", "Low"];

function RiskHeatmap({ register }: { register: RiskRegister }) {
  return (
    <div className="overflow-x-auto">
      <div className="grid min-w-[520px] grid-cols-[110px_repeat(3,1fr)] gap-1 text-xs">
        <div />
        {IMPACT_COLS.map((c) => (
          <div key={c} className="text-center font-medium text-ink-500">
            Impact: {c}
          </div>
        ))}
        {LIKELIHOOD_ROWS.map((row) => (
          <Fragment key={row}>
            <div className="flex items-center justify-end pr-2 font-medium text-ink-500">Likelihood: {row}</div>
            {IMPACT_COLS.map((col) => {
              const risks = register.risks.filter((r) => r.likelihood === row && r.impact === col);
              return (
                <div
                  key={`${row}-${col}`}
                  className={`min-h-[80px] rounded-md p-2 ${risks.length > 0 ? riskCellClasses(row, col) : "bg-ink-50 text-ink-300"}`}
                >
                  {risks.length === 0 ? (
                    <span>—</span>
                  ) : (
                    <ul className="space-y-0.5">
                      {risks.map((r, i) => (
                        <li key={i} className="truncate font-medium" title={r.description}>
                          {r.category}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              );
            })}
          </Fragment>
        ))}
      </div>
      <p className="mt-2 text-xs text-ink-400">
        Likelihood and impact are qualitative analytical judgements, not measured probabilities.
      </p>
    </div>
  );
}

export function RiskTab({ register }: { register: RiskRegister }) {
  return (
    <div className="space-y-6">
      <RiskHeatmap register={register} />

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-ink-200 text-left text-xs uppercase tracking-wide text-ink-500">
              <th className="py-2 pr-3">Category</th>
              <th className="py-2 pr-3">Risk</th>
              <th className="py-2 pr-3">Likelihood</th>
              <th className="py-2 pr-3">Impact</th>
              <th className="py-2 pr-3">Mitigation</th>
              <th className="py-2 pr-3">Owner</th>
            </tr>
          </thead>
          <tbody>
            {register.risks.map((r, i) => (
              <tr key={i} className="border-b border-ink-100 align-top">
                <td className="py-3 pr-3 font-medium text-ink-900">{r.category}</td>
                <td className="py-3 pr-3 text-ink-700">
                  {r.description}
                  {r.evidence && <div className="mt-1 text-xs italic text-ink-400">Evidence: {r.evidence}</div>}
                </td>
                <td className="py-3 pr-3">
                  <LevelBadge level={r.likelihood} />
                </td>
                <td className="py-3 pr-3">
                  <LevelBadge level={r.impact} />
                </td>
                <td className="py-3 pr-3 text-ink-700">{r.mitigation}</td>
                <td className="py-3 pr-3 text-ink-700">{r.owner}</td>
              </tr>
            ))}
            {register.risks.length === 0 && (
              <tr>
                <td colSpan={6} className="py-4 text-center text-ink-400">
                  No risks identified.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-ink-400">{register.note}</p>
    </div>
  );
}
