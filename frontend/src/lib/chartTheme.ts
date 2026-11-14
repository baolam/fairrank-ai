// Shared Plotly theme for the FairRank-AI quick-demo charts.
// Two measured signals only: teal = utility/accuracy, amber = fairness penalty/mitigation.
// Red is reserved for the recommended/flagged point, never used as a third routine series color.
export const CHART_INK = {
  primary: '#171b18',
  secondary: '#52594f',
  grid: '#dde3d8',
  baseline: '#c7d0c3',
}

export const CHART_SIGNAL = {
  teal: '#0d7a72',
  tealSoft: '#7fb8b3',
  amber: '#a66a0c',
  amberSoft: '#d9a860',
  alert: '#b23a3a',
}

export const CHART_FONT = { family: '"IBM Plex Mono", ui-monospace, monospace', color: CHART_INK.primary, size: 12 }

export const CHART_AXIS_BASE = {
  gridcolor: CHART_INK.grid,
  zerolinecolor: CHART_INK.baseline,
  tickfont: { color: CHART_INK.secondary },
}
