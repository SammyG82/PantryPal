import React, { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import type { Recipe } from '../types'

const UNICODE_FRACS: Record<string, number> = {
  '½': 0.5, '¼': 0.25, '¾': 0.75,
  '⅓': 1 / 3, '⅔': 2 / 3,
  '⅛': 0.125, '⅜': 0.375, '⅝': 0.625, '⅞': 0.875,
}

const NICE_FRACS: [number, string][] = [
  [1 / 8, '⅛'], [1 / 4, '¼'], [1 / 3, '⅓'], [3 / 8, '⅜'],
  [1 / 2, '½'], [5 / 8, '⅝'], [2 / 3, '⅔'], [3 / 4, '¾'], [7 / 8, '⅞'],
]

function snapFraction(f: number): string | null {
  const eps = 0.04
  for (const [val, sym] of NICE_FRACS) {
    if (Math.abs(f - val) < eps) return sym
  }
  return null
}

function formatQty(n: number): string {
  if (n <= 0) return ''
  const whole = Math.floor(n)
  const frac = n - whole
  if (frac < 0.01) return String(whole)
  const snap = snapFraction(frac)
  if (snap !== null) return whole > 0 ? `${whole} ${snap}` : snap
  return parseFloat(n.toFixed(2)).toString()
}

const UNICODE_RANGE = Object.keys(UNICODE_FRACS).join('')
const QTY_RE = new RegExp(
  `^(\\d+(?:\\.\\d+)?)\\s+([${UNICODE_RANGE}])|` +
  `^(\\d+)\\s+(\\d+)\\/(\\d+)|` +
  `^([${UNICODE_RANGE}])|` +
  `^(\\d+)\\/(\\d+)|` +
  `^(\\d+(?:\\.\\d+)?)`
)

function scaleIngredient(raw: string, multiplier: number): string {
  if (multiplier === 1) return raw
  const m = raw.match(QTY_RE)
  if (!m) return raw
  let qty: number
  if (m[1] !== undefined && m[2] !== undefined) {
    qty = parseInt(m[1], 10) + (UNICODE_FRACS[m[2]] ?? 0)
  } else if (m[3] !== undefined) {
    qty = parseInt(m[3], 10) + parseInt(m[4], 10) / parseInt(m[5], 10)
  } else if (m[6] !== undefined) {
    qty = UNICODE_FRACS[m[6]] ?? 0
  } else if (m[7] !== undefined) {
    qty = parseInt(m[7], 10) / parseInt(m[8], 10)
  } else {
    qty = parseFloat(m[9])
  }
  if (!isFinite(qty) || qty === 0) return raw
  return formatQty(qty * multiplier) + raw.slice(m[0].length)
}

const PRESETS = [0.5, 1, 5, 10]
const STEP = 0.5
const MIN = 0.5
const MAX = 10

interface Props {
  recipe: Recipe
  onClose: () => void
}

export default function ScaleModal({ recipe, onClose }: Props) {
  const [multiplier, setMultiplier] = useState(1)
  const ingredients = recipe.ingredients ?? []
  const modalRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  useEffect(() => {
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = prev }
  }, [])

  useEffect(() => {
    const modal = modalRef.current
    if (!modal) return
    const focusable = Array.from(modal.querySelectorAll<HTMLElement>('button:not([disabled])'))
    if (focusable.length === 0) return
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    const trap = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus() }
      } else {
        if (document.activeElement === last) { e.preventDefault(); first.focus() }
      }
    }
    document.addEventListener('keydown', trap)
    return () => document.removeEventListener('keydown', trap)
  }, [])

  return createPortal(
    <div className="scale-overlay" onClick={onClose}>
      <div
        ref={modalRef}
        className="info-modal scale-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="scale-modal-title"
        onClick={e => e.stopPropagation()}
      >
        <div className="info-modal-header">
          <span id="scale-modal-title" className="info-modal-title">{recipe.name}</span>
          <button className="info-close" autoFocus onClick={onClose} aria-label="Close">×</button>
        </div>

        <div className="scale-controls">
          <div className="scale-presets">
            {PRESETS.map(p => (
              <button
                key={p}
                className={`scale-preset-btn${multiplier === p ? ' active' : ''}`}
                onClick={() => setMultiplier(p)}
              >
                {p}×
              </button>
            ))}
          </div>
          <div className="scale-stepper">
            <button
              className="scale-step-btn"
              aria-label="Decrease"
              disabled={multiplier <= MIN}
              onClick={() => setMultiplier(m => +(m - STEP).toFixed(1))}
            >−</button>
            <span className="scale-display">{multiplier}×</span>
            <button
              className="scale-step-btn"
              aria-label="Increase"
              disabled={multiplier >= MAX}
              onClick={() => setMultiplier(m => +(m + STEP).toFixed(1))}
            >+</button>
          </div>
        </div>

        <div className="scale-ing-list">
          {ingredients.length === 0 ? (
            <p className="scale-ing-empty">Ingredient list not available for this recipe.</p>
          ) : (
            <ul>
              {ingredients.map((ing, i) => (
                <li key={i}>{scaleIngredient(ing, multiplier)}</li>
              ))}
            </ul>
          )}
        </div>

        <div className="scale-nutrition">
          <div className="scale-nutrition-item">
            <span className="scale-nutrition-val">{recipe.calories ? Math.round(recipe.calories * multiplier) : '–'}</span>
            <span className="scale-nutrition-key">kcal</span>
          </div>
          <div className="scale-nutrition-item">
            <span className="scale-nutrition-val">{recipe.protein ? `${Math.round(recipe.protein * multiplier)}g` : '–'}</span>
            <span className="scale-nutrition-key">protein</span>
          </div>
          <div className="scale-nutrition-item">
            <span className="scale-nutrition-val">{recipe.fat ? `${Math.round(recipe.fat * multiplier)}g` : '–'}</span>
            <span className="scale-nutrition-key">fat</span>
          </div>
          <div className="scale-nutrition-item">
            <span className="scale-nutrition-val">{recipe.carbs ? `${Math.round(recipe.carbs * multiplier)}g` : '–'}</span>
            <span className="scale-nutrition-key">carbs</span>
          </div>
        </div>
      </div>
    </div>,
    document.body
  )
}
