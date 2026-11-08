import { useEffect, useRef } from 'react'
import { echarts, type Option } from '../lib/echarts'

interface Props {
  option: Option
  height: number
  className?: string
  ariaLabel: string
  onClick?: (params: { dataIndex: number; seriesIndex: number; data: unknown; name: string }) => void
}

/** Thin ECharts wrapper: SVG renderer, resize-aware, no merge between renders. */
export function Chart({ option, height, className = '', ariaLabel, onClick }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const chart = useRef<ReturnType<typeof echarts.init> | null>(null)
  const clickRef = useRef(onClick)
  useEffect(() => {
    clickRef.current = onClick
  }, [onClick])

  useEffect(() => {
    if (!ref.current) return
    const instance = echarts.init(ref.current, undefined, { renderer: 'svg' })
    chart.current = instance
    instance.on('click', (p) => clickRef.current?.(p as never))
    const ro = new ResizeObserver(() => instance.resize())
    ro.observe(ref.current)
    return () => {
      ro.disconnect()
      instance.dispose()
      chart.current = null
    }
  }, [])

  useEffect(() => {
    chart.current?.setOption(option, { notMerge: true })
  }, [option])

  return <div ref={ref} role="img" aria-label={ariaLabel} className={className} style={{ height, width: '100%' }} />
}
