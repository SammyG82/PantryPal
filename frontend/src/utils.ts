const _apiUrl = import.meta.env.VITE_API_URL
if (!_apiUrl) throw new Error('VITE_API_URL is not set — check your .env file')
export const API: string = _apiUrl

export function toTitleCase(s: string): string {
  return s
    .trim()
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase())
}
