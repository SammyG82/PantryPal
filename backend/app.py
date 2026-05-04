# backend/app.py
from __future__ import annotations

import io
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

# -------------------------------------------------
# App setup
# -------------------------------------------------
app = FastAPI(title="PantryPal API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Lazy-load heavy dependencies so startup is fast
# even if the model isn't present
# -------------------------------------------------
_df = None


def get_df():
    global _df
    if _df is None:
        from recipe_search import load_recipes, _build_inverted_index
        _df = load_recipes()
        _build_inverted_index(_df)
    return _df


@app.on_event("startup")
def preload():
    get_df()


def get_predictor():
    """Return predict_image function, loading model on first call."""
    from utils.image_predict import predict_image
    return predict_image


# -------------------------------------------------
# Request / Response models
# -------------------------------------------------
class RecipesRequest(BaseModel):
    ingredients: List[str]


class RecipeResponse(BaseModel):
    id: int
    name: str
    match_score: int
    health_score: int
    calories: int
    protein: float
    fat: float
    carbs: float
    cook_time: str
    matched_count: int
    total_ingredients: int
    tags: List[str]
    url: str


class DetectResponse(BaseModel):
    ingredients: List[str]


# -------------------------------------------------
# Response helpers
# -------------------------------------------------
def _parse_cook_time(raw: str) -> str:
    value = (raw or "").strip()
    return value if value and value != "nan" else "N/A"


def _tags_from_health(health_score_pct: int) -> List[str]:
    if health_score_pct >= 75:
        return ["Healthy"]
    elif health_score_pct >= 50:
        return ["Balanced"]
    else:
        return ["Indulgent"]


def _to_recipe_response(r: dict) -> RecipeResponse:
    health_pct = round(r["health_score"] * 100)
    return RecipeResponse(
        id=r["id"],
        name=r["name"],
        match_score=round(r["score"] * 100),
        health_score=health_pct,
        calories=r.get("calories", 0) or 0,
        protein=round(r.get("protein_g", 0.0) or 0.0, 1),
        fat=round(r.get("fat_g", 0.0) or 0.0, 1),
        carbs=round(r.get("carbs_g", 0.0) or 0.0, 1),
        cook_time=_parse_cook_time(r.get("cook_time", "") or ""),
        matched_count=r["matches"],
        total_ingredients=r["recipe_size"],
        tags=_tags_from_health(health_pct),
        url=r.get("url", "") or "",
    )


# -------------------------------------------------
# Endpoints
# -------------------------------------------------
@app.get("/")
def root():
    return {"message": "PantryPal API is running"}


@app.post("/api/detect", response_model=DetectResponse)
async def detect_ingredients(file: UploadFile = File(...)):
    """
    Accept a multipart image upload, run the CNN, return detected ingredient(s).
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read image: {e}")

    try:
        predict_image = get_predictor()
        label = predict_image(image)
        ingredients = [label] if label else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model inference failed: {e}")

    return DetectResponse(ingredients=ingredients)


class CorrectRequest(BaseModel):
    ingredient: str


class CorrectResponse(BaseModel):
    corrected: str
    found: bool


class SearchRequest(BaseModel):
    q: str
    ingredients: List[str] = []


@app.post("/api/correct", response_model=CorrectResponse)
def correct_ingredient_endpoint(body: CorrectRequest):
    from recipe_search import correct_ingredient
    df = get_df()
    corrected, found = correct_ingredient(body.ingredient, df)
    return CorrectResponse(corrected=corrected, found=found)


@app.post("/api/search", response_model=List[RecipeResponse])
def search_recipes(body: SearchRequest):
    if not body.q.strip():
        return []

    from recipe_search import search_by_name

    df = get_df()
    results = search_by_name(body.q, df, user_ings=body.ingredients or None)

    return [_to_recipe_response(r) for r in results]


@app.post("/api/recipes", response_model=List[RecipeResponse])
def get_recipes(body: RecipesRequest):
    """
    Accept a list of ingredients, return ranked recipe matches.
    """
    if not body.ingredients:
        raise HTTPException(status_code=400, detail="No ingredients provided")

    from recipe_search import match_recipes

    df = get_df()
    results = match_recipes(body.ingredients, df)

    return [_to_recipe_response(r) for r in results]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
