export function Sidebar() {
  return (
    <aside className="hidden w-72 shrink-0 flex-col gap-6 border-r border-gray-200 bg-white p-6 lg:flex">
      <div>
        <div className="text-lg font-bold text-gray-900">🛡️ FairRank-AI</div>
        <p className="mt-1 text-xs text-gray-500">
          Enterprise Algorithmic Fairness &amp; Audit Engine
        </p>
      </div>

      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-400">
          Core Capabilities
        </h3>
        <ul className="mt-2 space-y-1.5 text-sm text-gray-600">
          <li>⚡ Information Retrieval: BM25, Sentence-BERT</li>
          <li>⚖️ Mitigation: Greedy Exposure-Aware Reranker, CDA</li>
          <li>🔍 Causal Audit: Counterfactual Invariance, PopResume PSE</li>
          <li>📑 Compliance: Holm-Bonferroni, EU AI Act Reporting</li>
        </ul>
      </section>

      <hr className="border-gray-200" />

      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-400">
          Architecture &amp; API
        </h3>
        <ul className="mt-2 space-y-1.5 text-sm text-gray-600">
          <li>
            🚀 REST API Docs:{' '}
            <a
              className="text-brand-600 underline"
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
            >
              localhost:8000/docs
            </a>
          </li>
          <li>⚛️ Frontend: React + Vite + TypeScript</li>
          <li>🐳 Dockerized: Backend + Frontend Multi-service</li>
        </ul>
      </section>
    </aside>
  )
}
