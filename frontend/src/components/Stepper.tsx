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
    <ol className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-stretch sm:gap-0">
      {STEPS.map((step) => {
        const isCompleted = step.id < currentStep
        const isCurrent = step.id === currentStep
        const isUnlocked = canNavigateTo(step.id)
        const clickable = isUnlocked && !isCurrent

        return (
          <li key={step.id} className="flex flex-1 flex-col">
            <button
              type="button"
              disabled={!clickable}
              onClick={() => clickable && onNavigate(step.id)}
              className={`flex w-full items-center gap-2.5 py-2 text-left transition-colors ${clickable ? 'cursor-pointer' : 'cursor-default'}`}
            >
              <span
                className={`fr-mono flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-[12px] ${
                  isCurrent
                    ? 'border-fr-teal bg-fr-teal text-white'
                    : isCompleted
                      ? 'border-fr-teal text-fr-teal'
                      : 'border-fr-line text-fr-ink-soft'
                }`}
              >
                {isCompleted ? '✓' : step.id}
              </span>
              <span>
                <span className={`block text-[13px] font-medium ${isCurrent ? 'text-fr-ink' : 'text-fr-ink-soft'}`}>
                  {step.label}
                </span>
                <span className="block text-[11px] text-fr-ink-soft">{step.description}</span>
              </span>
            </button>
            <span
              className={`mt-1 h-[3px] w-full rounded-full ${
                isCurrent || isCompleted ? 'bg-fr-teal' : 'bg-fr-line'
              }`}
              aria-hidden
            />
          </li>
        )
      })}
    </ol>
  )
}
