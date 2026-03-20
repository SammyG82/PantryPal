import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import NavBar from '../components/NavBar'
import UploadZone, { type UploadZoneHandle } from '../components/UploadZone'
import IngredientInput from '../components/IngredientInput'
import IngredientChip from '../components/IngredientChip'

function Home() {
  const [typedIngredients, setTypedIngredients] = useState<string[]>([])
  const [detectedIngredients, setDetectedIngredients] = useState<string[]>([])
  const navigate = useNavigate()
  const uploadZoneRef = useRef<UploadZoneHandle>(null)

  const allIngredients = [
    ...typedIngredients,
    ...detectedIngredients.filter(
      (d) => !typedIngredients.some((t) => t.toLowerCase() === d.toLowerCase())
    ),
  ]

  const addIngredient = (value: string) => {
    const trimmed = value.trim()
    if (!trimmed) return
    if (allIngredients.some((i) => i.toLowerCase() === trimmed.toLowerCase())) return
    setTypedIngredients((prev) => [...prev, trimmed])
  }

  const removeIngredient = (index: number) => {
    setTypedIngredients((prev) => prev.filter((_, i) => i !== index))
  }

  const handleDetected = (detectedList: string[]) => {
    setDetectedIngredients(detectedList)
  }

  const handleCook = () => {
    if (allIngredients.length === 0) return
    navigate('/results', { state: { ingredients: allIngredients } })
  }

  return (
    <div>
      <NavBar ingredients={allIngredients} />

      <div className="home-hero">
        <div className="eyebrow">✨ AI-powered recipe matching</div>
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
              <UploadZone ref={uploadZoneRef} onDetectedChange={handleDetected} />
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
                  typedIngredients.map((ing, i) => (
                    <IngredientChip
                      key={ing + i}
                      label={ing}
                      onRemove={() => removeIngredient(i)}
                    />
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="cook-footer">
            <div className="total-count">
              <div className="footer-label">
                <strong>{allIngredients.length}</strong> ingredient{allIngredients.length !== 1 ? 's' : ''} added
              </div>
              {allIngredients.length > 0 && (
                <div className="footer-chips">
                  {typedIngredients.map((ing, i) => (
                    <IngredientChip key={ing + i} label={ing} onRemove={() => removeIngredient(i)} />
                  ))}
                  {detectedIngredients.filter(d => !typedIngredients.some(t => t.toLowerCase() === d.toLowerCase())).map((ing) => (
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
