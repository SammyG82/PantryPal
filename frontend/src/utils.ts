export const API = import.meta.env.VITE_API_URL ?? ''

export function toTitleCase(s: string): string {
  return s
    .trim()
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase())
}
