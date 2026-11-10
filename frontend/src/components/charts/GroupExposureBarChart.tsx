import Plot from 'react-plotly.js'
import type { GroupSummaryOutput } from '../../types/api'
import { GROUP_LABELS, INTERSECTIONAL_GROUPS } from '../../types/api'

const INK = {
  primary: '#0b0b0b',
  secondary: '#52514e',
  grid: '#e1e0d9',
  baseline: '#c3c2b7',
}
const SERIES = { exposure: '#2a78d6', selection: '#eb6834' }

interface GroupExposureBarChartProps {
  summaries: GroupSummaryOutput[]
}

export function GroupExposureBarChart({ summaries }: GroupExposureBarChartProps) {
  const byGroup = new Map(summaries.map((s) => [s.group, s]))
  const labels = INTERSECTIONAL_GROUPS.map((g) => GROUP_LABELS[g])
  const exposure = INTERSECTIONAL_GROUPS.map((g) => byGroup.get(g)?.mean_exposure_at_10 ?? 0)
  const selection = INTERSECTIONAL_GROUPS.map((g) => byGroup.get(g)?.selection_rate_at_10 ?? 0)

  return (
    <Plot
      data={[
        {
          type: 'bar',
          name: 'Mean Exposure @10',
          x: labels,
          y: exposure,
          marker: { color: SERIES.exposure },
          text: exposure.map((v) => v.toFixed(3)),
          textposition: 'outside',
        },
        {
          type: 'bar',
          name: 'Selection Rate @10',
          x: labels,
          y: selection,
          marker: { color: SERIES.selection },
          text: selection.map((v) => v.toFixed(3)),
          textposition: 'outside',
        },
      ]}
      layout={{
        barmode: 'group',
        height: 360,
        margin: { l: 48, r: 16, t: 16, b: 48 },
        font: { family: 'system-ui, sans-serif', color: INK.primary, size: 12 },
        legend: { orientation: 'h', y: -0.2 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: { linecolor: INK.baseline, tickfont: { color: INK.secondary } },
        yaxis: {
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
