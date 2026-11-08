import { useState, type ReactNode } from 'react'

export function Card({ title, subtitle, action, children, className = '' }: {
  title?: ReactNode
  subtitle?: ReactNode
  action?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`card ${className}`}>
      {(title || action) && (
        <header className="mb-3 flex items-start justify-between gap-3">
          <div>
            {title && <h3 className="text-[15px] font-semibold text-ink">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-xs text-muted">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      {children}
    </section>
  )
}

export function Stat({ label, value, unit, delta, deltaGood, hint, accent }: {
  label: string
  value: string
  unit?: string
  delta?: string
  /** true = good news, false = bad news, undefined = neutral */
  deltaGood?: boolean
  hint?: string
  accent?: string
}) {
  return (
    <div className="card flex flex-col gap-1" title={hint}>
      <div className="flex items-center gap-2 text-xs font-medium text-ink-2">
        {accent && <span className="h-2 w-2 rounded-full" style={{ background: accent }} aria-hidden />}
        {label}
      </div>
      <div className="text-2xl font-semibold tracking-tight text-ink">
        {value}
        {unit && <span className="ml-1 text-sm font-normal text-muted">{unit}</span>}
      </div>
      {delta && (
        <div
          className={`text-xs ${deltaGood === true ? 'text-good-text' : deltaGood === false ? 'text-critical' : 'text-muted'}`}
        >
          {deltaGood === true ? '▲ ' : deltaGood === false ? '▼ ' : ''}
          {delta}
        </div>
      )}
    </div>
  )
}

export function Segmented<T extends string>({ value, options, onChange, label }: {
  value: T
  options: { key: T; label: string }[]
  onChange: (v: T) => void
  label: string
}) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex rounded-full border border-line bg-surface p-0.5">
      {options.map((o) => (
        <button
          key={o.key}
          role="radio"
          aria-checked={value === o.key}
          onClick={() => onChange(o.key)}
          className={`rounded-full px-3 py-1 text-xs font-medium transition ${
            value === o.key ? 'bg-ink text-page' : 'text-ink-2 hover:bg-surface-2'
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

export function Chip({ active, onClick, children, color }: {
  active: boolean
  onClick: () => void
  children: ReactNode
  color?: string
}) {
  return (
    <button
      onClick={onClick}
      aria-pressed={active}
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition ${
        active ? 'border-transparent bg-ink text-page' : 'border-line text-ink-2 hover:bg-surface-2'
      }`}
    >
      {color && <span className="h-2 w-2 rounded-full" style={{ background: color }} aria-hidden />}
      {children}
    </button>
  )
}

/**
 * Illustration from web/public/img (WebP); hidden if missing.
 * `tile` sets scene illustrations on the same night-blue tile in both themes, so their soft
 * glows never look smudged on a light page.
 */
export function Illustration({ name, alt, className = '', tile = false }: {
  name: string
  alt: string
  className?: string
  tile?: boolean
}) {
  const [ok, setOk] = useState(true)
  if (!ok) return null
  const img = (
    <img
      src={`${import.meta.env.BASE_URL}img/${name}.webp`}
      alt={alt}
      className={tile ? 'h-full w-full object-contain' : `object-contain ${className}`}
      loading="lazy"
      decoding="async"
      onError={() => setOk(false)}
    />
  )
  return tile ? <span className={`block overflow-hidden rounded-2xl bg-[#1b1638] ${className}`}>{img}</span> : img
}

export function Legend({ items }: { items: { label: string; color: string; shape?: 'dot' | 'line' }[] }) {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-2">
      {items.map((i) => (
        <li key={i.label} className="flex items-center gap-1.5">
          <span
            aria-hidden
            className={i.shape === 'line' ? 'h-0.5 w-3 rounded' : 'h-2 w-2 rounded-full'}
            style={{ background: i.color }}
          />
          {i.label}
        </li>
      ))}
    </ul>
  )
}

export function Note({ children }: { children: ReactNode }) {
  return <p className="text-xs leading-relaxed text-muted">{children}</p>
}
