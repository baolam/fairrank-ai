import type { WizardStep } from '../store/useRankingStore'

interface StepDef {
  id: WizardStep
  label: string
  description: string
}

const STEPS: StepDef[] = [
  { id: 1, label: 'Upload dữ liệu', description: 'JD & hồ sơ ứng viên' },
  { id: 2, label: 'Cấu hình & Chạy', description: 'Model, redaction, λ' },
  { id: 3, label: 'Kết quả & So sánh', description: 'Ranking, Pareto, Audit' },
]

interface StepperProps {
  currentStep: WizardStep
  canNavigateTo: (step: WizardStep) => boolean
  onNavigate: (step: WizardStep) => void
}

export function Stepper({ currentStep, canNavigateTo, onNavigate }: StepperProps) {
  return (
    <ol className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-stretch sm:gap-0">
      {STEPS.map((step, idx) => {
        const isCompleted = step.id < currentStep
        const isCurrent = step.id === currentStep
        const isUnlocked = canNavigateTo(step.id)
        const clickable = isUnlocked && !isCurrent

        return (
          <li key={step.id} className="flex flex-1 items-center">
            <button
              type="button"
              disabled={!clickable}
              onClick={() => clickable && onNavigate(step.id)}
              className={`flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left transition-colors ${
                isCurrent
                  ? 'border-brand-600 bg-brand-50'
                  : isCompleted
                    ? 'border-emerald-200 bg-emerald-50 hover:bg-emerald-100'
                    : 'border-gray-200 bg-gray-50 opacity-60'
              } ${clickable ? 'cursor-pointer' : 'cursor-default'}`}
            >
              <span
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${
                  isCurrent
                    ? 'bg-brand-600 text-white'
                    : isCompleted
                      ? 'bg-emerald-600 text-white'
                      : 'bg-gray-300 text-gray-600'
                }`}
              >
                {isCompleted ? '✓' : step.id}
              </span>
              <span>
                <span
                  className={`block text-sm font-semibold ${
                    isCurrent ? 'text-brand-700' : isCompleted ? 'text-emerald-800' : 'text-gray-500'
                  }`}
                >
                  {step.label}
                </span>
                <span className="block text-xs text-gray-500">{step.description}</span>
              </span>
            </button>
            {idx < STEPS.length - 1 && (
              <span className="mx-2 hidden h-px w-6 shrink-0 bg-gray-300 sm:block" aria-hidden />
            )}
          </li>
        )
      })}
    </ol>
  )
}
