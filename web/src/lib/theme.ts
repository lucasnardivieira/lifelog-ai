import { useEffect, useState } from 'react'

export type ThemeChoice = 'system' | 'light' | 'dark'

const TOKENS = [
  'page', 'surface', 'surface-2', 'ink', 'ink-2', 'muted', 'grid', 'axis', 'border',
  'area-body', 'area-mind', 'area-growth', 'area-money',
  'q-yellow', 'q-red', 'q-blue', 'q-green',
  'good', 'warning', 'serious', 'critical',
  'seq-1', 'seq-2', 'seq-3', 'seq-4', 'seq-5', 'seq-6', 'seq-7',
  'div-mid', 'div-neg', 'div-pos',
  'cat-1', 'cat-2', 'cat-3', 'cat-4', 'cat-5', 'cat-6', 'cat-7',
] as const
export type Token = (typeof TOKENS)[number]
export type Tokens = Record<Token, string> & { dark: boolean }

function read(): Tokens {
  const cs = getComputedStyle(document.documentElement)
  const t = Object.fromEntries(TOKENS.map((k) => [k, cs.getPropertyValue(`--${k}`).trim()])) as Record<Token, string>
  return { ...t, dark: cs.colorScheme.includes('dark') }
}

/** Resolved CSS tokens for chart options; re-reads when the theme or OS scheme changes. */
export function useTokens(): Tokens {
  const [tokens, setTokens] = useState<Tokens>(read)
  useEffect(() => {
    const update = () => setTokens(read())
    const mq = matchMedia('(prefers-color-scheme: dark)')
    mq.addEventListener('change', update)
    const mo = new MutationObserver(update)
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    return () => {
      mq.removeEventListener('change', update)
      mo.disconnect()
    }
  }, [])
  return tokens
}

export function getThemeChoice(): ThemeChoice {
  const t = document.documentElement.dataset.theme
  return t === 'light' || t === 'dark' ? t : 'system'
}

export function setThemeChoice(choice: ThemeChoice) {
  if (choice === 'system') delete document.documentElement.dataset.theme
  else document.documentElement.dataset.theme = choice
  try {
    if (choice === 'system') localStorage.removeItem('lifelog:theme')
    else localStorage.setItem('lifelog:theme', choice)
  } catch {
    /* storage unavailable */
  }
}

export const AREA_TOKEN = {
  body: 'area-body',
  mind: 'area-mind',
  growth: 'area-growth',
  money_social: 'area-money',
} as const

export const QUADRANT_TOKEN = {
  yellow: 'q-yellow',
  red: 'q-red',
  blue: 'q-blue',
  green: 'q-green',
} as const

export const QUADRANT_EMOJI = { yellow: '⚡', red: '🌩️', blue: '🌧️', green: '🍃' } as const
export const QUADRANT_SHORT = {
  yellow: 'Agradável · energia alta',
  red: 'Desagradável · energia alta',
  blue: 'Desagradável · energia baixa',
  green: 'Agradável · energia baixa',
} as const

/** Categorical slots in fixed order (validated adjacent-pair CVD order). Never cycle past 7. */
export const CAT: Token[] = ['cat-1', 'cat-2', 'cat-3', 'cat-4', 'cat-5', 'cat-6', 'cat-7']
