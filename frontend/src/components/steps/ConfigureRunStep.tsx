import { useRef, useState } from 'react'
import { executeRanking } from '../../lib/apiClient'
import { useRankingStore } from '../../store/useRankingStore'
import { GROUP_LABELS } from '../../types/api'
import type { ModelName } from '../../types/api'
import { PipelineDiagram, type PipelineStageDef, type PipelineStageStatus } from '../PipelineDiagram'

type ModelOption = 'bm25' | 'rerank' | 'sbert'
type RunPhase = 'idle' | 'running' | 'done'

const MODEL_OPTIONS: { value: ModelOption; label: string }[] = [
  { value: 'bm25', label: 'BM25 (Lexical Baseline)' },
  { value: 'rerank', label: 'Greedy Fair Reranker (Exposure-Aware)' },
  { value: 'sbert', label: 'Sentence-BERT (all-mpnet-base-v2)' },
]

const STAGE_SEQUENCE = [0, 1, 2, 3]
const STAGE_STEP_MS = 450

export function ConfigureRunStep() {
  const jobTitle = useRankingStore((s) => s.jobTitle)
  const jobDescription = useRankingStore((s) => s.jobDescription)
  const candidatesPool = useRankingStore((s) => s.candidatesPool)
  const setStep = useRankingStore((s) => s.setStep)
  const setLastRun = useRankingStore((s) => s.setLastRun)

  const [modelOption, setModelOption] = useState<ModelOption>('bm25')
  const [redaction, setRedaction] = useState(false)
  const [lambdaVal, setLambdaVal] = useState(0)
  const [cutoffK, setCutoffK] = useState(10)
  const [runError, setRunError] = useState<string | null>(null)

  const [phase, setPhase] = useState<RunPhase>('idle')
  const [activeStageIndex, setActiveStageIndex] = useState<number>(-1)
  const seqPosRef = useRef(0)

  function handleModelChange(value: ModelOption) {
    setModelOption(value)
    if (value === 'rerank' && lambdaVal === 0) {
      setLambdaVal(1.5)
    }
  }

  // The actual scorer that runs is always BM25 or SBERT — "Greedy Fair Reranker" is a
  // convenience dropdown shortcut that just bumps λ (see handleModelChange), not a scoring
  // model. Label the scoring stage and the saved run with the real scorer, never the shortcut.
  const modelLabel = modelOption === 'sbert' ? 'Sentence-BERT (all-mpnet-base-v2)' : 'BM25 (Lexical Baseline)'
  const rerankActive = lambdaVal > 0
  const activeSequence = rerankActive ? STAGE_SEQUENCE : STAGE_SEQUENCE.filter((i) => i !== 1)

  const stageDefs: PipelineStageDef[] = [
    {
      id: 'score',
      icon: '📥',
      label: 'Chấm điểm (Scoring)',
      detail: `Mô hình: ${modelLabel}${redaction ? ' · Redaction ON — ẩn tên trước khi chấm' : ''}`,
      formula: modelOption === 'sbert' ? 'score = cosine(JD, mean-pool chunk embeddings)' : 'BM25Okapi(k1=1.2, b=0.75)',
    },
    {
      id: 'rerank',
      icon: '⚖️',
      label: 'Tái xếp hạng công bằng',
      detail: rerankActive ? `λ = ${lambdaVal.toFixed(1)} · top-${cutoffK}` : 'Không áp dụng vì λ = 0',
      formula: 'argmax (Δutility − λ·Δdisparity) theo từng vị trí',
    },
    {
      id: 'metrics',
      icon: '📏',
      label: 'Đo hiệu suất (Utility)',
      detail: 'nDCG@k & MRR trên thứ tự cuối cùng',
      formula: 'nDCG = DCG / IDCG, MRR = 1/rank(Good Fit đầu tiên)',
    },
    {
      id: 'audit',
      icon: '🔍',
      label: 'Kiểm toán thiên lệch',
      detail: 'Exposure trung bình theo 4 nhóm giao nhau',
      formula: 'e(rank) = 1/log2(rank+1); gap = mean(nhóm A) − mean(nhóm B)',
    },
  ]

  function getStatus(stageIdx: number): PipelineStageStatus {
    if (stageIdx === 1 && !rerankActive) return 'skipped'
    if (phase === 'idle') return 'pending'
    if (phase === 'done') return 'done'
    const seqPos = activeSequence.indexOf(stageIdx)
    const curSeqPos = activeSequence.indexOf(activeStageIndex)
    if (seqPos === -1) return 'pending'
    if (seqPos < curSeqPos) return 'done'
    if (seqPos === curSeqPos) return 'active'
    return 'pending'
  }

  const statuses = stageDefs.map((_, idx) => getStatus(idx))

  async function handleRun() {
    if (candidatesPool.length === 0) return
    setRunError(null)
    setPhase('running')
    seqPosRef.current = 0
    setActiveStageIndex(activeSequence[0])
    const timer = window.setInterval(() => {
      seqPosRef.current += 1
      if (seqPosRef.current < activeSequence.length) {
        setActiveStageIndex(activeSequence[seqPosRef.current])
      }
    }, STAGE_STEP_MS)

    try {
      const modelName: ModelName = modelOption === 'sbert' ? 'sbert' : 'bm25'
      const result = await executeRanking({
        job_description: jobDescription,
        candidates: candidatesPool.map((c) => ({
          id: c.id,
          name: c.name,
          text: redaction && c.redacted_text ? c.redacted_text : c.resume,
          group: c.group,
          relevance_grade: c.relevance_grade,
        })),
        model_name: modelName,
        redaction_enabled: redaction,
        lambda_penalty: lambdaVal > 0 ? lambdaVal : null,
        cutoff_k: cutoffK,
      })
      window.clearInterval(timer)
      setPhase('done')
      await new Promise((resolve) => setTimeout(resolve, 350))
      setLastRun({
        jobTitle,
        jobDescription,
        modelLabel,
        modelName,
        lambdaVal,
        cutoffK,
        redactionEnabled: redaction,
        candidatesPool,
        ranking: result,
      })
      setStep(3)
    } catch (err) {
      window.clearInterval(timer)
      setPhase('idle')
      setRunError(err instanceof Error ? err.message : 'Ranking pipeline failed.')
    }
  }

  const running = phase !== 'idle'

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-fr-ink">Bước 2 · Cấu hình &amp; chạy xử lý</h2>
        <p className="mt-1 text-sm text-fr-ink-soft">
          Chọn mô hình xếp hạng và tham số công bằng, sau đó chạy pipeline đánh giá.
        </p>
      </div>

      <div className="rounded-md border border-fr-line bg-white p-4 text-sm text-fr-ink-soft">
        <p>
          <span className="text-fr-ink">Job title:</span> {jobTitle || '—'}
        </p>
        <p className="mt-1">
          <span className="text-fr-ink">Candidate pool:</span>{' '}
          <span className="fr-mono text-fr-ink">{candidatesPool.length}</span> hồ sơ (
          {Array.from(new Set(candidatesPool.map((c) => GROUP_LABELS[c.group]))).join(', ') || 'chưa có dữ liệu'})
        </p>
        <button type="button" className="mt-2 text-sm font-medium text-fr-teal hover:text-fr-ink" onClick={() => setStep(1)}>
          ← Sửa lại dữ liệu
        </button>
      </div>

      <div className="flex flex-wrap items-end gap-5">
        <label className="text-sm font-medium text-fr-ink-soft">
          Ranking engine
          <select
            className="mt-1 block rounded-md border border-fr-line bg-white px-3 py-2 text-sm text-fr-ink focus:border-fr-teal focus:outline-none"
            value={modelOption}
            onChange={(e) => handleModelChange(e.target.value as ModelOption)}
          >
            {MODEL_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        <label className="flex items-center gap-2 text-sm font-medium text-fr-ink-soft">
          <input
            type="checkbox"
            checked={redaction}
            onChange={(e) => setRedaction(e.target.checked)}
            className="accent-fr-teal"
          />
          Enable sensitive redaction
        </label>

        <label className="text-sm font-medium text-fr-ink-soft">
          Fairness penalty λ (<span className="fr-mono text-fr-amber">{lambdaVal.toFixed(1)}</span>)
          <input
            type="range"
            min={0}
            max={5}
            step={0.1}
            value={lambdaVal}
            onChange={(e) => setLambdaVal(Number(e.target.value))}
            className="mt-1.5 block w-40 accent-fr-amber"
          />
        </label>

        <label className="text-sm font-medium text-fr-ink-soft">
          Top-K cutoff
          <input
            type="number"
            min={1}
            max={20}
            value={cutoffK}
            onChange={(e) => setCutoffK(Number(e.target.value))}
            className="mt-1 block w-20 rounded-md border border-fr-line bg-white px-2 py-2 text-sm text-fr-ink focus:border-fr-teal focus:outline-none"
          />
        </label>
      </div>

      <div>
        <h3 className="text-sm font-medium text-fr-ink">Pipeline sẽ chạy qua các giai đoạn sau</h3>
        <div className="mt-2.5">
          <PipelineDiagram stages={stageDefs} statuses={statuses} />
        </div>
      </div>

      {runError && <p className="text-sm text-fr-alert">{runError}</p>}

      <div className="flex items-center justify-between border-t border-fr-line pt-4">
        <button type="button" className="text-sm font-medium text-fr-ink-soft hover:text-fr-ink" onClick={() => setStep(1)}>
          ← Quay lại
        </button>
        <button
          type="button"
          onClick={handleRun}
          disabled={running || candidatesPool.length === 0}
          className="rounded-md bg-fr-teal px-5 py-2.5 text-sm font-medium text-white hover:bg-fr-ink transition-colors disabled:cursor-not-allowed disabled:opacity-40"
        >
          {phase === 'running' ? 'Đang chạy…' : phase === 'done' ? 'Hoàn tất ✓' : 'Run ranking & audit pipeline'}
        </button>
      </div>
    </div>
  )
}
