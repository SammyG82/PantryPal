# PantryPal

A web app that suggests recipes based on ingredients you have. Type ingredients in or upload a photo — the app matches them against 231k recipes and ranks results by ingredient overlap or nutrition score.

---

## Tech Stack

| Component | Technology |
|---|---|
| **Frontend** | React + TypeScript (Vite) |
| **Backend** | Python, FastAPI |
| **Image Recognition** | OpenCLIP ViT-B-32 (fine-tuned), PyTorch |
| **Matching** | pandas, rapidfuzz |
| **Deployment** | Vercel (frontend) + HuggingFace Spaces (backend) |

---

## Features

- Type ingredients — autocorrected against recipe vocabulary, unsupported ones flagged
- Upload a photo per ingredient — CLIP model predicts the label
- Fuzzy ingredient matching (e.g. `chopped onions` ≈ `onions`)
- Sort by **Best Match** (ingredient overlap) or **Healthiest** (nutrition score)
- Info modal explaining scoring, recipe name search, direct links to full recipes
- Responsive across mobile, tablet, and desktop

---

## Scoring

**Best Match** — `0.6 × pct_recipe + 0.25 × pct_user + 0.15 × jaccard`

**Healthiest** — `0.45 × protein + 0.25 × low_sugar + 0.30 × low_calories`

---

## Model

| Property | Value |
|---|---|
| **Architecture** | CLIP ViT-B-32 + custom classification head |
| **Classes** | 46 ingredients |
| **Accuracy** | ~94% on test set |
| **File** | `Food_Recognition_Model_94.pt` (~351MB) — auto-downloaded from `SammyG82/Single_Ingredient_Identification` at startup |

---

## Dataset

| Property | Value |
|---|---|
| **Source** | Food.com Recipes (Kaggle) |
| **Size** | 231,637 recipes |
| **File** | `recipes.csv` (~80MB) — auto-downloaded from `SammyG82/pantrypal-data` at startup |

---

## Running Locally

```bash
npm install
npm run dev
# Backend → http://localhost:8000
# Frontend → http://localhost:5173
```

Create `frontend/.env`:
```
VITE_API_URL=http://localhost:8000
```

The model and dataset download automatically on first run (~430MB total). No token required.

---

## Deployment

| | Service |
|---|---|
| **Frontend** | Vercel — `pantry-pal-kohl.vercel.app` |
| **Backend** | HuggingFace Spaces — `SammyG82-pantrypal.hf.space` |

Backend is synced via `scripts/push-backend.sh`.
