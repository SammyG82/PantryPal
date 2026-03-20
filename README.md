# PantryPal

---

## Project Overview

> **Goal:** Create a web app that suggests recipes based on the ingredients users already have. Users can either *type them in* or *upload a photo* of each ingredient. It uses a fine-tuned **CLIP ViT-B-32** model for image-based ingredient detection and *fuzzy string matching* to recommend and rank recipes based on *ingredient overlap* and *available nutrition metadata*.

---

## Tech Stack

| Component | Technology |
|---|---|
| **Frontend/UI** | React + TypeScript (Vite) |
| **Styling** | Custom CSS — "Editorial Kitchen" design system |
| **Routing** | React Router |
| **Backend API** | Python, FastAPI |
| **Image Recognition** | OpenCLIP ViT-B-32 (fine-tuned), PyTorch |
| **Pre Processing** | Pillow (PIL), torchvision |
| **Matching Logic** | Python, pandas, rapidfuzz |
| **Deployment** | Vercel (frontend) + HuggingFace Spaces (backend) |
| **Version Control** | Git + GitHub |

---

## Core Features

- Text-based ingredient input — add one at a time, press Enter or click Add
- Image-based ingredient detection — upload a photo per ingredient, CLIP model predicts the label
- Bidirectional photo ↔ ingredient sync — removing a photo removes its detected ingredient and vice versa
- Fuzzy ingredient matching (e.g., `chopped onions` ≈ `onions`)
- Recipe ranking based on ingredient overlap score
- Secondary ranking based on health score derived from nutrition metadata
- Duplicate ingredient detection — silently ignored across both typed and detected inputs
- Responsive web interface

---

## Workflow

1. **User Input:**
   - Type ingredients one at a time (Enter or Add button)
   - Upload one photo per ingredient — model auto-detects the label
   - Duplicate items (typed or detected) automatically ignored
   - Each item has a remove button; removing a photo also removes its ingredient chip

2. **Ingredient Normalization:**
   - Text cleanup: `"chopped tomato"` → `"tomato"`
   - CLIP model inference: image → ingredient label (46 possible classes)
   - Typed and detected ingredients combined for recipe matching

3. **Recipe Matching:**
   - Searches through `recipes.csv`
   - Computes fuzzy similarity for each ingredient
   - Calculates match score (ingredient overlap %) and health score (from nutrition metadata)

4. **Ranking & Display:**
   - Sort by Best Match (ingredient overlap %) or Healthiest First (health score)
   - Recipe cards show rank, score, tags, macros, cook time, servings

---

## Model

| Property | Value |
|---|---|
| **Architecture** | CLIP ViT-B-32 visual encoder + custom classification head |
| **Classes** | 46 ingredients |
| **Accuracy** | ~94% on test set |
| **Training data** | `Scuccorese/food-ingredients-dataset` (HuggingFace), 80/20 stratified split |
| **Model file** | `Food_Recognition_Model_94.pt` (~351MB) — stored at `SammyG82/Single_Ingredient_Identification` (public), auto-downloaded at startup |

The model is a **single-label classifier** — it predicts one ingredient per image. For multiple ingredients, upload one photo per ingredient.

---

## Project Structure

```
PantryPal/
├── frontend/                        # React + TypeScript (Vite)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.tsx             # Ingredient input page
│   │   │   └── Results.tsx          # Recipe results page
│   │   ├── components/
│   │   │   ├── NavBar.tsx
│   │   │   ├── UploadZone.tsx       # Photo upload + ingredient detection
│   │   │   ├── IngredientInput.tsx  # Text input for ingredients
│   │   │   ├── IngredientChip.tsx   # Removable ingredient pill
│   │   │   ├── RecipeCard.tsx       # Recipe result card
│   │   │   └── SortBar.tsx          # Sort toggle (match / health)
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── types.ts                 # Shared TypeScript types
│   │   └── index.css                # Global styles + design system
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── backend/                         # Python FastAPI server
│   ├── app.py                       # API entry point
│   ├── recipe_search.py             # Fuzzy matching + ranking logic
│   ├── Dockerfile                   # For HuggingFace Spaces deployment
│   ├── model/
│   │   ├── Food_Recognition_Model_94.pt   # CLIP model weights (gitignored, auto-downloaded)
│   │   └── label_map.json                 # Index → ingredient name map
│   ├── utils/
│   │   └── image_predict.py         # CLIP model loading + inference
│   └── requirements.txt
│
├── data/
│   └── raw/
│       └── recipes.csv              # Recipe dataset (ingredients + nutrition)
│
├── .gitignore
└── README.md
```

---

## Running Locally

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
# Runs on http://localhost:8000
```

The model downloads automatically from HuggingFace on first run (~351MB). No token required — the model repo is public.

### Frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

Create `frontend/.env`:
```
VITE_API_URL=http://localhost:8000
```

---

## Deployment

| | Service | URL |
|---|---|---|
| **Frontend** | Vercel | `pantry-pal-kohl.vercel.app` |
| **Backend** | HuggingFace Spaces | `SammyG82-pantrypal.hf.space` |

- Frontend env var: `VITE_API_URL=https://SammyG82-pantrypal.hf.space`
- Backend Space repo: `huggingface.co/spaces/SammyG82/pantrypal` (separate from this GitHub repo)
- No secrets required — model repo is public
