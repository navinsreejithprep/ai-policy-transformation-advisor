export function Header() {
  return (
    <header className="border-b border-ink-200 bg-white">
      <div className="mx-auto max-w-6xl px-6 py-6">
        <div className="text-xs font-semibold uppercase tracking-widest text-brand-600">
          AI Strategy &amp; Transformation Advisory Platform
        </div>
        <h1 className="mt-1 text-3xl font-semibold text-ink-900">AI Policy &amp; Transformation Advisor</h1>
        <p className="mt-1 max-w-2xl text-sm text-ink-600">
          Evidence-backed policy analysis and implementation planning — RAG-grounded, multi-agent, independently reviewed.
        </p>
      </div>
    </header>
  );
}

export function Disclaimer() {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      <strong className="font-semibold">AI-generated analysis</strong> — verify critical decisions against primary
      sources. This is a portfolio proof-of-concept; do not treat outputs as production-grade advice.
    </div>
  );
}
