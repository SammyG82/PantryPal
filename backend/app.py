# backend/app.py
from __future__ import annotations

import io
import re
from pathlib import Path
from typing import List, Optional

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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Lazy-load heavy dependencies so startup is fast
# even if the model isn't present
# -------------------------------------------------
_df = None
_model_loaded = False


def get_df():
    global _df
    if _df is None:
        from recipe_search import load_recipes
        _df = load_recipes()
    return _df


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
    servings: Optional[int]
    matched_count: int
    total_ingredients: int
    tags: List[str]


class DetectResponse(BaseModel):
    ingredients: List[str]


# -------------------------------------------------
# Tag helper
# -------------------------------------------------
def _tags_from_health(health_score_pct: int) -> List[str]:
    if health_score_pct >= 75:
        return ["Healthy"]
    elif health_score_pct >= 50:
        return ["Balanced"]
    else:
        return ["Indulgent"]


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


@app.post("/api/recipes", response_model=List[RecipeResponse])
def get_recipes(body: RecipesRequest):
    """
    Accept a list of ingredients, return ranked recipe matches.
    """
    if not body.ingredients:
        raise HTTPException(status_code=400, detail="No ingredients provided")

    from recipe_search import match_recipes

    df = get_df()
    results = match_recipes(body.ingredients, df, quota=10)

    response: List[RecipeResponse] = []
    for r in results:
        health_pct = round(r["health_score"] * 100)
        match_pct = round(r["score"] * 100)

        # Parse cook_time: prefer first number + "min", else use as-is or "N/A"
        cook_time_raw = r.get("cook_time", "") or ""
        if cook_time_raw and cook_time_raw.strip() and cook_time_raw.strip() != "nan":
            cook_time = cook_time_raw.strip()
        else:
            cook_time = "N/A"

        response.append(
            RecipeResponse(
                id=r["id"],
                name=r["name"],
                match_score=match_pct,
                health_score=health_pct,
                calories=r.get("calories", 0) or 0,
                protein=round(r.get("protein_g", 0.0) or 0.0, 1),
                fat=round(r.get("fat_g", 0.0) or 0.0, 1),
                carbs=round(r.get("carbs_g", 0.0) or 0.0, 1),
                cook_time=cook_time,
                servings=r.get("servings"),
                matched_count=r["matches"],
                total_ingredients=r["recipe_size"],
                tags=_tags_from_health(health_pct),
            )
        )

    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
