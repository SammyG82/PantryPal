import React, { useRef, useState, useMemo } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import NavBar from '../components/NavBar'
import UploadZone, { type UploadZoneHandle } from '../components/UploadZone'
import IngredientInput from '../components/IngredientInput'
import IngredientChip from '../components/IngredientChip'
import type { Upload } from '../types'

interface HomeProps {
  typedIngredients: string[]
  setTypedIngredients: React.Dispatch<React.SetStateAction<string[]>>
  uploads: Upload[]
  setUploads: React.Dispatch<React.SetStateAction<Upload[]>>
}

function Home({ typedIngredients, setTypedIngredients, uploads, setUploads }: HomeProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const lastIngredients: string[] | undefined = location.state?.lastIngredients
  const uploadZoneRef = useRef<UploadZoneHandle>(null)
  const [unsupported, setUnsupported] = useState<Set<string>>(new Set())
  const [recent] = useState<{ ingredients: string[]; unsupported: string[] } | null>(() => {
    try {
      const saved = localStorage.getItem('pantrypal_recent')
      if (!saved) return null
      const parsed = JSON.parse(saved)
      const age = Date.now() - (parsed.savedAt ?? 0)
      if (age > 24 * 60 * 60 * 1000 || !Array.isArray(parsed.ingredients) || !Array.isArray(parsed.unsupported)) {
        localStorage.removeItem('pantrypal_recent')
        return null
      }
      return parsed
    } catch {
      return null
    }
  })

  const detectedIngredients = useMemo(
    () => [...new Set(uploads.filter((u) => u.ingredient !== null && !u.detecting).map((u) => u.ingredient as string))],
    [uploads]
  )

  const allIngredients = useMemo(
    () => [
      ...typedIngredients,
      ...detectedIngredients.filter((d) => !typedIngredients.some((t) => t.toLowerCase() === d.toLowerCase())),
    ],
    [typedIngredients, detectedIngredients]
  )

  const addIngredient = (value: string, supported: boolean) => {
    const trimmed = value.trim()
    if (!trimmed) return
    if (allIngredients.some((i) => i.toLowerCase() === trimmed.toLowerCase())) return
    setTypedIngredients((prev) => [...prev, trimmed])
    if (!supported) setUnsupported((prev) => new Set(prev).add(trimmed))
  }

  const removeIngredient = (ing: string) => {
    setTypedIngredients((prev) => prev.filter((i) => i !== ing))
    setUnsupported((u) => { const next = new Set(u); next.delete(ing); return next })
  }

  const handleCook = () => {
    if (allIngredients.length === 0) return
    const prevIngredients = recent?.ingredients ?? []
    const prevUnsupported = recent?.unsupported ?? []
    const merged = [
      ...allIngredients,
      ...prevIngredients.filter(
        (p) => !allIngredients.some((a) => a.toLowerCase() === p.toLowerCase())
      ),
    ].slice(0, 20)
    try {
      localStorage.setItem('pantrypal_recent', JSON.stringify({
        ingredients: merged,
        unsupported: [...new Set([...unsupported, ...prevUnsupported])],
        savedAt: Date.now(),
      }))
    } catch { /* quota / private mode — skip recent save */ }
    navigate('/results', { state: { ingredients: allIngredients.slice(0, 20) } })
  }

  const recentAvailable = useMemo(
    () => recent?.ingredients.filter((r) => !allIngredients.some((i) => i.toLowerCase() === r.toLowerCase())) ?? [],
    [recent, allIngredients]
  )

  return (
    <div>
      <NavBar ingredients={allIngredients} lastIngredients={lastIngredients} />

      <div className="home-hero">
        <div className="eyebrow">✨ ML-powered recipe matching</div>
        <h1>
          What's in your<br />
          <em>kitchen today?</em>
        </h1>
        <p>
          Upload a photo or type your ingredients — we'll find the best recipes you can make right now.
        </p>
      </div>

      <div className="input-section">
        <div className="input-card">
          <div className="input-cols">
            <div className="input-col">
              <div className="col-title">Upload a photo</div>
              <p className="col-sub">
                Snap an individual ingredient from your fridge or pantry. Our AI will detect the ingredients automatically.
              </p>
              <UploadZone
                ref={uploadZoneRef}
                initialUploads={uploads}
                onUploadsChange={setUploads}
              />
            </div>

            <div className="input-divider">
              <div className="or-badge">or</div>
            </div>

            <div className="input-col">
              <div className="col-title">Type ingredients</div>
              <p className="col-sub">
                Add one ingredient at a time. Press Enter or click Add.
              </p>
              <IngredientInput onAdd={addIngredient} />
              <div className="chip-list">
                {typedIngredients.length === 0 ? (
                  <span className="empty-hint">Your ingredients will appear here…</span>
                ) : (
                  typedIngredients.map((ing) => (
                    <IngredientChip
                      key={ing}
                      label={ing}
                      unsupported={unsupported.has(ing)}
                      onRemove={() => removeIngredient(ing)}
                    />
                  ))
                )}
              </div>
              {recentAvailable.length > 0 && (
                <div className="recent-row">
                  <span className="recent-label">Recently used</span>
                  <div className="recent-chips">
                    {recentAvailable.map((ing) => (
                      <button
                        key={ing}
                        className="recent-chip"
                        onClick={() => addIngredient(ing, !recent!.unsupported.includes(ing))}
                      >
                        + {ing}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="cook-footer">
            <div className="total-count">
              <div className="footer-label">
                <strong>{allIngredients.length}</strong> ingredient{allIngredients.length !== 1 ? 's' : ''} added
              </div>
              {allIngredients.length > 0 && (
                <div className="footer-chips">
                  {typedIngredients.map((ing) => (
                    <IngredientChip key={ing} label={ing} unsupported={unsupported.has(ing)} onRemove={() => removeIngredient(ing)} />
                  ))}
                  {detectedIngredients
                    .filter((d) => !typedIngredients.some((t) => t.toLowerCase() === d.toLowerCase()))
                    .map((ing) => (
                      <IngredientChip key={ing} label={ing} onRemove={() => uploadZoneRef.current?.removeByIngredient(ing)} />
                    ))}
                </div>
              )}
            </div>
            <button
              className="cook-btn"
              disabled={allIngredients.length === 0}
              onClick={handleCook}
            >
              Cook! →
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home
