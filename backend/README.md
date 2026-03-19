# PantryPal — Backend

FastAPI server for ingredient detection and recipe matching.

## Stack
- **FastAPI** — API framework
- **CLIP ViT-B-32** (`open_clip`) — ingredient image classification (46 classes, ~94% accuracy)
- **rapidfuzz** — fuzzy ingredient matching against recipes.csv
- **pandas** — recipe dataset handling

## Endpoints

### `POST /api/detect`
Accepts a single image upload, returns the detected ingredient.
```
Body: multipart/form-data, field: "file"
Returns: { "ingredients": ["spinach"] }
```

### `POST /api/recipes`
Accepts a list of ingredients, returns ranked recipe matches.
```
Body: { "ingredients": ["spinach", "chicken", "garlic"] }
Returns: [ { "id", "name", "match_score", "health_score", "calories", ... } ]
```

## Running locally

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

Runs on `http://localhost:8000`. The model (`Food_Recognition_Model_94.pt`) auto-downloads from HuggingFace on first run — requires `HF_TOKEN` set in a `.env` file.

## Environment variables

Create a `.env` file in this directory:
```
HF_TOKEN=your_huggingface_token
```
