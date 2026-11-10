import Plot from 'react-plotly.js'
import type { GroupScoreSummary } from '../../types/api'
import { GROUP_LABELS, type IntersectionalGroup } from '../../types/api'

const INK = {
  primary: '#0b0b0b',
  secondary: '#52514e',
  grid: '#e1e0d9',
  baseline: '#c3c2b7',
}
const SERIES = { baseline: '#2a78d6', mitigated: '#1baf7a' }

interface CounterfactualBoxPlotProps {
  baseline: GroupScoreSummary[]
  mitigated: GroupScoreSummary[]
}

function groupLabel(group: string): string {
  return GROUP_LABELS[group as IntersectionalGroup] ?? group
}

export function CounterfactualBoxPlot({ baseline, mitigated }: CounterfactualBoxPlotProps) {
  return (
    <Plot
      data={[
        {
          type: 'box',
          name: 'Baseline (Unmitigated)',
          x: baseline.flatMap((g) => g.scores.map(() => groupLabel(g.group))),
          y: baseline.flatMap((g) => g.scores),
          marker: { color: SERIES.baseline },
          boxpoints: 'all',
          jitter: 0.4,
        },
        {
          type: 'box',
          name: 'Mitigated (Redaction / Invariant)',
          x: mitigated.flatMap((g) => g.scores.map(() => groupLabel(g.group))),
          y: mitigated.flatMap((g) => g.scores),
          marker: { color: SERIES.mitigated },
          boxpoints: 'all',
          jitter: 0.4,
        },
      ]}
      layout={{
        boxmode: 'group',
        height: 420,
        margin: { l: 56, r: 16, t: 24, b: 56 },
        font: { family: 'system-ui, sans-serif', color: INK.primary, size: 12 },
        legend: { orientation: 'h', y: -0.2 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: { linecolor: INK.baseline, tickfont: { color: INK.secondary } },
        yaxis: {
          title: { text: 'BM25 Score' },
          gridcolor: INK.grid,
          zerolinecolor: INK.baseline,
          tickfont: { color: INK.secondary },
        },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%' }}
    />
  )
}
