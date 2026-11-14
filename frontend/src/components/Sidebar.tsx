import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

function RailSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-l-2 border-fr-line pl-3">
      <h3 className="text-[13px] font-medium text-fr-ink-soft">{title}</h3>
      <div className="mt-2">{children}</div>
    </section>
  )
}

export function Sidebar() {
  return (
    <aside className="hidden w-72 shrink-0 flex-col gap-7 border-r border-fr-line bg-fr-paper p-6 lg:flex">
      <div>
        <div className="text-[17px] font-semibold text-fr-ink">FairRank-AI</div>
        <p className="fr-mono mt-1 text-[11px] text-fr-ink-soft">audit instrument · ats engine</p>
      </div>

      <RailSection title="Hệ thống ATS tuyển dụng">
        <nav className="space-y-0.5 text-sm">
          <Link
            to="/recruiter"
            className="block rounded px-2 py-1.5 text-fr-ink-soft hover:bg-fr-teal-soft hover:text-fr-teal transition-colors"
          >
            Quản lý tin tuyển dụng
          </Link>
          <Link
            to="/talent-pool"
            className="block rounded px-2 py-1.5 text-fr-ink-soft hover:bg-fr-teal-soft hover:text-fr-teal transition-colors"
          >
            Kho tài năng (Talent Pool)
          </Link>
          <Link
            to="/apply"
            className="block rounded px-2 py-1.5 text-fr-ink-soft hover:bg-fr-teal-soft hover:text-fr-teal transition-colors"
          >
            Cổng ứng viên (/apply)
          </Link>
          <Link
            to="/quick-demo"
            className="block rounded px-2 py-1.5 font-medium text-fr-teal bg-fr-teal-soft"
          >
            Quick Audit Simulator
          </Link>
        </nav>
      </RailSection>

      <RailSection title="Core capabilities">
        <ul className="fr-mono space-y-1.5 text-[11.5px] text-fr-ink-soft">
          <li>Retrieval: BM25, SBERT</li>
          <li>Mitigation: Greedy Exposure Reranker</li>
          <li>Causal audit: PopResume PSE, Invariance</li>
          <li>Compliance: EU AI Act &amp; EEOC 4/5ths Rule</li>
        </ul>
      </RailSection>

      <RailSection title="Architecture & API">
        <ul className="fr-mono space-y-1.5 text-[11.5px] text-fr-ink-soft">
          <li>
            REST API docs:{' '}
            <a
              className="text-fr-teal underline decoration-fr-line underline-offset-2"
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
            >
              /docs
            </a>
          </li>
          <li>Frontend: React + Vite + TypeScript</li>
          <li>Docker multi-service ready</li>
        </ul>
      </RailSection>
    </aside>
  )
}
