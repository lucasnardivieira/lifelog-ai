import type { Payload } from '../types'

const base = import.meta.env.BASE_URL

/** Private data (gitignored, local only) wins over the public synthetic demo. */
export async function loadPayload(): Promise<Payload> {
  for (const file of ['data/lifelog.local.json', 'data/lifelog.json']) {
    try {
      const res = await fetch(`${base}${file}`)
      if (res.ok && res.headers.get('content-type')?.includes('json')) return await res.json()
    } catch {
      /* try next */
    }
  }
  throw new Error('Não encontrei os dados. Rode `uv run lifelog build`.')
}
