import type { DocumentCategory } from "@/types/api";

// Purely informational — never enforced. A user can upload anything, in any tab,
// or skip categorizing entirely; the backend defaults an uncategorized upload to
// "other" and it works exactly the same as any other document.
export const DOCUMENT_CATEGORIES: { value: DocumentCategory; label: string; hint: string }[] = [
  {
    value: "policy",
    label: "Policy Document",
    hint: "The policy or programme text itself — objectives, target groups, mechanisms.",
  },
  {
    value: "evidence",
    label: "Evidence & Research",
    hint: "Surveys, studies, or data that support or challenge the policy's assumptions.",
  },
  {
    value: "benchmark",
    label: "Benchmarks",
    hint: "How comparable programmes elsewhere approached a similar problem.",
  },
  {
    value: "risk",
    label: "Risk Precedents",
    hint: "Case studies of what went wrong (or right) in similar past rollouts.",
  },
  {
    value: "stakeholder",
    label: "Stakeholder Input",
    hint: "Consultation notes, feedback, or positions from affected groups.",
  },
  {
    value: "budget",
    label: "Budget & Governance",
    hint: "Funding structure, governance model, or approval process documents.",
  },
  {
    value: "other",
    label: "Other",
    hint: "Anything else worth including — no need to force-fit a category.",
  },
];

export function categoryLabel(value: DocumentCategory): string {
  return DOCUMENT_CATEGORIES.find((c) => c.value === value)?.label ?? "Other";
}
