import Plot from 'react-plotly.js'
import type { GroupSummaryOutput } from '../../types/api'
import { GROUP_LABELS, INTERSECTIONAL_GROUPS } from '../../types/api'
import { CHART_AXIS_BASE, CHART_FONT, CHART_SIGNAL } from '../../lib/chartTheme'

const SERIES = { exposure: CHART_SIGNAL.teal, selection: CHART_SIGNAL.amber }

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
        font: CHART_FONT,
        legend: { orientation: 'h', y: -0.2 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: { linecolor: CHART_AXIS_BASE.zerolinecolor, tickfont: CHART_AXIS_BASE.tickfont },
        yaxis: CHART_AXIS_BASE,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%' }}
    />
  )
}
