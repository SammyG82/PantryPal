const _apiUrl = import.meta.env.VITE_API_URL
if (!_apiUrl) throw new Error('VITE_API_URL is not set — check your .env file')
export const API: string = _apiUrl

export function toTitleCase(s: string): string {
  return s
    .trim()
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

// Backend returns 503 while the recipe data / model are still warming up
// (e.g. after the HF Space wakes from sleep). onWaking fires after 4s —
// above the ~1s normal response time — so it only shows for genuine cold
// starts, and one retry gives the warm-up a second chance to land.
export async function apiFetch(
  url: string,
  options: RequestInit,
  onWaking?: () => void,
): Promise<Response> {
  const slowTimer = setTimeout(() => onWaking?.(), 4000)
  try {
    let res = await fetch(url, options)
    if (res.status === 503 && !options.signal?.aborted) {
      await new Promise((resolve) => setTimeout(resolve, 3000))
      if (!options.signal?.aborted) res = await fetch(url, options)
    }
    return res
  } finally {
    clearTimeout(slowTimer)
  }
}
