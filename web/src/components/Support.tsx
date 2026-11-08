import { useEffect, useRef } from 'react'
import { useLife } from '../lib/context'
import { Illustration } from './ui'

export function SupportCard({ compact = false }: { compact?: boolean }) {
  const { payload } = useLife()
  const s = payload.support
  return (
    <div className="card flex gap-4" role="note" aria-label={s.title}>
      {!compact && <Illustration name="support" alt="" tile className="hidden h-20 w-20 shrink-0 sm:block" />}
      <div className="space-y-2">
        <h3 className="font-semibold">💬 {s.title}</h3>
        <p className="text-sm text-ink-2">{s.text}</p>
        <ul className="flex flex-wrap gap-2">
          {s.contacts.map((c) => (
            <li key={c.name}>
              <a
                href={c.href}
                target={c.href.startsWith('http') ? '_blank' : undefined}
                rel="noreferrer"
                className="inline-flex flex-col rounded-xl border border-line px-3 py-2 text-sm hover:bg-surface-2"
              >
                <span className="font-medium text-ink">{c.name}</span>
                <span className="text-xs text-ink-2">{c.detail}</span>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export function SupportDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (open && !d.open) d.showModal()
    if (!open && d.open) d.close()
  }, [open])
  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(e) => e.target === ref.current && onClose()}
      className="m-auto w-[min(560px,calc(100vw-32px))] rounded-2xl bg-transparent p-0 backdrop:bg-black/50"
    >
      <div className="relative">
        <SupportCard />
        <button onClick={onClose} className="absolute right-3 top-3 text-muted hover:text-ink" aria-label="Fechar">
          ✕
        </button>
      </div>
    </dialog>
  )
}
