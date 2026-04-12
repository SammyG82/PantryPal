import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Results from './pages/Results'
import type { Upload } from './types'

function App() {
  const [typedIngredients, setTypedIngredients] = useState<string[]>([])
  const [uploads, setUploads] = useState<Upload[]>([])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={
          <Home
            typedIngredients={typedIngredients}
            setTypedIngredients={setTypedIngredients}
            uploads={uploads}
            setUploads={setUploads}
          />
        } />
        <Route path="/results" element={<Results />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
