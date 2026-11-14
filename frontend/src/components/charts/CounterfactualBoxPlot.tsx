import Plot from 'react-plotly.js'
import type { GroupScoreSummary } from '../../types/api'
import { GROUP_LABELS, type IntersectionalGroup } from '../../types/api'
import { CHART_AXIS_BASE, CHART_FONT, CHART_SIGNAL } from '../../lib/chartTheme'

const SERIES = { baseline: CHART_SIGNAL.amber, mitigated: CHART_SIGNAL.teal }

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
        font: CHART_FONT,
        legend: { orientation: 'h', y: -0.2 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: { linecolor: CHART_AXIS_BASE.zerolinecolor, tickfont: CHART_AXIS_BASE.tickfont },
        yaxis: { title: { text: 'BM25 Score' }, ...CHART_AXIS_BASE },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%' }}
    />
  )
}
