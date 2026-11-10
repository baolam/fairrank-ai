import Plot from 'react-plotly.js'
import type { ParetoPoint } from '../../types/api'

const INK = {
  primary: '#0b0b0b',
  secondary: '#52514e',
  grid: '#e1e0d9',
  baseline: '#c3c2b7',
}
const OPTIMAL_RED = '#e34948'
const SEQUENTIAL_BLUE: [number, string][] = [
  [0, '#cde2fb'],
  [0.5, '#2a78d6'],
  [1, '#0d366b'],
]

export interface ParetoRow extends ParetoPoint {
  utility_retention: number
}

interface ParetoScatterChartProps {
  rows: ParetoRow[]
  optimal: ParetoRow
}

export function ParetoScatterChart({ rows, optimal }: ParetoScatterChartProps) {
  return (
    <Plot
      data={[
        {
          type: 'scatter',
          mode: 'markers',
          x: rows.map((r) => r.black_white_exposure_gap),
          y: rows.map((r) => r.ndcg_at_k),
          text: rows.map(
            (r) =>
              `λ=${r.lambda_penalty} · utility retention ${r.utility_retention.toFixed(1)}% · F-M gap ${r.female_male_exposure_gap.toFixed(3)} · intersectional excess ${r.intersectional_excess.toFixed(3)}`,
          ),
          hoverinfo: 'text',
          marker: {
            size: rows.map((r) => Math.max(10, r.utility_retention / 4)),
            color: rows.map((r) => r.lambda_penalty),
            colorscale: SEQUENTIAL_BLUE,
            showscale: true,
            colorbar: { title: { text: 'λ' } },
            line: { width: 1, color: '#fcfcfb' },
          },
          name: 'λ grid',
        },
        {
          type: 'scatter',
          mode: 'markers+text',
          x: [optimal.black_white_exposure_gap],
          y: [optimal.ndcg_at_k],
          marker: { symbol: 'star', size: 20, color: OPTIMAL_RED },
          text: ['⭐ Recommended λ'],
          textposition: 'top center',
          textfont: { color: OPTIMAL_RED },
          name: 'Optimal point',
          hoverinfo: 'skip',
        },
      ]}
      layout={{
        height: 440,
        margin: { l: 56, r: 16, t: 24, b: 56 },
        font: { family: 'system-ui, sans-serif', color: INK.primary, size: 12 },
        showlegend: true,
        legend: { orientation: 'h', y: -0.2 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: {
          title: { text: 'Black-White Exposure Gap (lower is fairer)' },
          gridcolor: INK.grid,
          zerolinecolor: INK.baseline,
          tickfont: { color: INK.secondary },
        },
        yaxis: {
          title: { text: 'nDCG@10 (higher is better)' },
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
