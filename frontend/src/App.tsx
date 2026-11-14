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
    <div className="fr-shell flex min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-x-hidden px-4 py-8 sm:px-8">
        <header className="mb-8 max-w-3xl">
          <Link to="/" className="text-sm font-medium text-fr-teal hover:text-fr-ink transition-colors">
            ← Về trang chủ
          </Link>
          <h1 className="mt-3 text-[1.7rem] font-semibold leading-tight text-fr-ink sm:text-3xl">
            FairRank-AI audit instrument
          </h1>
          <p className="mt-2 text-[15px] leading-relaxed text-fr-ink-soft">
            Measures algorithmic accountability, bias mitigation, and utility preservation across a resume-ranking
            pipeline — scoring, exposure-aware reranking, and demographic-parity audit in one run.
          </p>
        </header>

        <Stepper currentStep={step} canNavigateTo={canNavigateTo} onNavigate={setStep} />

        <section className="rounded-lg border border-fr-line bg-fr-raised p-6">
          {step === 1 && <UploadDataStep />}
          {step === 2 && <ConfigureRunStep />}
          {step === 3 && <ResultsCompareStep />}
        </section>
      </main>
    </div>
  )
}

export default App
