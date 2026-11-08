import { BarChart, CustomChart, HeatmapChart, LineChart, RadarChart, ScatterChart } from 'echarts/charts'
import {
  AxisPointerComponent,
  CalendarComponent,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  MarkLineComponent,
  RadarComponent,
  TooltipComponent,
  VisualMapComponent,
} from 'echarts/components'
import * as echarts from 'echarts/core'
import { SVGRenderer } from 'echarts/renderers'
import type { Tokens } from './theme'

echarts.use([
  BarChart, CustomChart, HeatmapChart, LineChart, RadarChart, ScatterChart,
  AxisPointerComponent, CalendarComponent, DataZoomComponent, GridComponent, LegendComponent,
  MarkAreaComponent, MarkLineComponent, RadarComponent, TooltipComponent, VisualMapComponent,
  SVGRenderer,
])

export { echarts }
// biome-ignore lint: echarts option objects are deeply dynamic
export type Option = Record<string, any>

export const FONT = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'

/** Shared chrome: recessive hairline grid/axes, ink-token text, readable tooltip. */
export function baseOption(t: Tokens): Option {
  return {
    backgroundColor: 'transparent',
    textStyle: { fontFamily: FONT, color: t['ink-2'], fontSize: 12 },
    animationDuration: 400,
    tooltip: {
      backgroundColor: t.surface,
      borderColor: t.border,
      borderWidth: 1,
      padding: [8, 10],
      textStyle: { color: t.ink, fontFamily: FONT, fontSize: 12 },
      extraCssText: 'border-radius:10px;box-shadow:0 6px 24px rgba(0,0,0,.18);',
    },
  }
}

export function axisStyle(t: Tokens) {
  return {
    axisLine: { lineStyle: { color: t.axis } },
    axisTick: { show: false },
    axisLabel: { color: t.muted, fontSize: 11, fontFamily: FONT },
    splitLine: { lineStyle: { color: t.grid, width: 1 } },
  }
}

export const dot = (color: string) =>
  `<span style="display:inline-block;width:8px;height:8px;border-radius:4px;background:${color};margin-right:6px"></span>`
