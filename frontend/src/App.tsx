import { Link } from 'react-router-dom'
import { Sidebar } from './components/Sidebar'
import { Stepper } from './components/Stepper'
import { UploadDataStep } from './components/steps/UploadDataStep'
import { ConfigureRunStep } from './components/steps/ConfigureRunStep'
import { ResultsCompareStep } from './components/steps/ResultsCompareStep'
import { useRankingStore, type WizardStep } from './store/useRankingStore'

function App() {
  const step = useRankingStore((s) => s.step)
  const setStep = useRankingStore((s) => s.setStep)
  const candidatesPool = useRankingStore((s) => s.candidatesPool)
  const lastRun = useRankingStore((s) => s.lastRun)

  function canNavigateTo(target: WizardStep) {
    if (target === 1) return true
    if (target === 2) return candidatesPool.length > 0
    if (target === 3) return lastRun !== null
    return false
  }

  return (
    <div className="flex min-h-screen bg-[#f6f5fb]">
      <Sidebar />
      <main className="flex-1 overflow-x-hidden px-4 py-8 sm:px-8">
        <header className="mb-6">
          <Link to="/" className="text-sm font-medium text-brand-700 underline">
            ← Về trang chủ
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-gray-900 sm:text-3xl">
            🛡️ FairRank-AI: Enterprise Audit &amp; Fairness-Aware Resume Ranking
          </h1>
          <p className="mt-2 max-w-3xl text-sm text-gray-600">
            An interactive AI auditing platform demonstrating <strong>Algorithmic Accountability, Bias Mitigation,
            and Utility Preservation</strong> in Automated Resume-Job Recommendation.
          </p>
        </header>

        <Stepper currentStep={step} canNavigateTo={canNavigateTo} onNavigate={setStep} />

        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          {step === 1 && <UploadDataStep />}
          {step === 2 && <ConfigureRunStep />}
          {step === 3 && <ResultsCompareStep />}
        </section>
      </main>
    </div>
  )
}

export default App
