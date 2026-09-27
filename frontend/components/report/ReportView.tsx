"use client";

import { useState } from "react";
import type { FinalReport } from "@/types/api";
import { ExecutiveSummaryTab } from "./ExecutiveSummaryTab";
import { EvidenceTab } from "./EvidenceTab";
import { StakeholderTab } from "./StakeholderTab";
import { RiskTab } from "./RiskTab";
import { BenchmarkTab } from "./BenchmarkTab";
import { RoadmapTab } from "./RoadmapTab";
import { KpiTab } from "./KpiTab";
import { SourcesTab } from "./SourcesTab";

const TABS = [
  "Executive Summary",
  "Evidence",
  "Stakeholders",
  "Risks",
  "Benchmarks",
  "Roadmap",
  "KPIs",
  "Sources",
] as const;

type Tab = (typeof TABS)[number];

export function ReportView({ report }: { report: FinalReport }) {
  const [active, setActive] = useState<Tab>("Executive Summary");

  return (
    <section className="card overflow-hidden">
      <div className="flex flex-wrap gap-1 border-b border-ink-200 bg-ink-50 px-3 pt-3">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActive(tab)}
            className={`rounded-t-md px-3 py-2 text-sm font-medium transition-colors ${
              active === tab
                ? "bg-white text-brand-700 border border-ink-200 border-b-white"
                : "text-ink-500 hover:text-ink-800"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>
      <div className="p-5">
        {active === "Executive Summary" && <ExecutiveSummaryTab report={report} />}
        {active === "Evidence" && <EvidenceTab evidence={report.evidence} />}
        {active === "Stakeholders" && <StakeholderTab matrix={report.stakeholders} />}
        {active === "Risks" && <RiskTab register={report.risks} />}
        {active === "Benchmarks" && <BenchmarkTab report={report.benchmarks} />}
        {active === "Roadmap" && <RoadmapTab plan={report.implementation} />}
        {active === "KPIs" && <KpiTab plan={report.implementation} />}
        {active === "Sources" && <SourcesTab sources={report.sources} />}
      </div>
    </section>
  );
}
