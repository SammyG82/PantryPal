# backend/app.py
from __future__ import annotations

import asyncio
import io
import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from pydantic import BaseModel, Field, StringConstraints
from PIL import Image

logger = logging.getLogger(__name__)

_IMAGE_MAGIC = (
    b'\xff\xd8\xff',       # JPEG
    b'\x89PNG\r\n\x1a\n',  # PNG
    b'GIF87a',             # GIF87
    b'GIF89a',             # GIF89
    b'RIFF',               # WebP
    b'BM',                 # BMP
    b'II*\x00',            # TIFF LE
    b'MM\x00*',            # TIFF BE
)

# -------------------------------------------------
# App setup
# -------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    get_df()
    get_predictor()
    yield


app = FastAPI(title="PantryPal API", version="1.0.0", lifespan=lifespan)

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


_predictor = None


def get_predictor():
    global _predictor
    if _predictor is None:
        from utils.image_predict import predict_image, load_model
        load_model()
        _predictor = predict_image
    return _predictor


# -------------------------------------------------
# Request / Response models
# -------------------------------------------------
_Ingredient = Annotated[str, StringConstraints(max_length=200)]

_VALID_DIETARY = frozenset({"vegetarian", "vegan", "gluten_free"})


class RecipesRequest(BaseModel):
    ingredients: List[_Ingredient]
    dietary: List[str] = []


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
    ingredients: List[str] = []
    missing_ingredients: List[str] = []
    dietary_flags: List[str] = []


class DetectResponse(BaseModel):
    ingredients: List[str]


# -------------------------------------------------
# Response helpers
# -------------------------------------------------
_TAG_HEALTHY = ["Healthy"]
_TAG_BALANCED = ["Balanced"]
_TAG_INDULGENT = ["Indulgent"]


def _tags_from_health(health_score_pct: int) -> List[str]:
    if health_score_pct >= 75:
        return _TAG_HEALTHY
    elif health_score_pct >= 50:
        return _TAG_BALANCED
    return _TAG_INDULGENT


def _get_dietary_valid_indices(df, dietary: list[str]):
    if not dietary:
        return None
    import pandas as pd
    mask = pd.Series(True, index=df.index)
    if "vegan" in dietary:
        mask &= df["is_vegan"]
    elif "vegetarian" in dietary:
        mask &= df["is_vegetarian"]
    if "gluten_free" in dietary:
        mask &= df["is_gluten_free"]
    return set(df.index[mask])


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
        cook_time=r.get("cook_time", "") or "",
        matched_count=r["matches"],
        total_ingredients=r["recipe_size"],
        tags=_tags_from_health(health_pct),
        url=r.get("url", "") or "",
        ingredients=r.get("ingredients_raw", []) or [],
        missing_ingredients=r.get("missing_raw", []) or [],
        dietary_flags=r.get("dietary_flags", []) or [],
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
        contents = await file.read(10 * 1024 * 1024 + 1)
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
        if not any(contents.startswith(m) for m in _IMAGE_MAGIC):
            raise HTTPException(status_code=400, detail="File must be a valid image")
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Image read failed")
        raise HTTPException(status_code=400, detail="Could not read image")

    try:
        predict_fn = get_predictor()
        label = await asyncio.get_running_loop().run_in_executor(None, predict_fn, image)
        ingredients = [label] if label else []
    except Exception:
        logger.exception("Model inference failed")
        raise HTTPException(status_code=500, detail="Model inference failed")

    return DetectResponse(ingredients=ingredients)


class CorrectRequest(BaseModel):
    ingredient: str = Field(..., max_length=200)


class CorrectResponse(BaseModel):
    corrected: str
    found: bool


class SearchRequest(BaseModel):
    q: str = Field(..., max_length=200)
    ingredients: List[_Ingredient] = []
    dietary: List[str] = []


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

    invalid = set(body.dietary) - _VALID_DIETARY
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid dietary filter(s): {sorted(invalid)}")

    from recipe_search import search_by_name

    df = get_df()
    valid_indices = _get_dietary_valid_indices(df, body.dietary)
    results = search_by_name(body.q, df, user_ings=body.ingredients or None, valid_indices=valid_indices)

    return [_to_recipe_response(r) for r in results]


@app.post("/api/recipes", response_model=List[RecipeResponse])
def get_recipes(body: RecipesRequest):
    if not body.ingredients:
        raise HTTPException(status_code=400, detail="No ingredients provided")
    if len(body.ingredients) > 50:
        raise HTTPException(status_code=400, detail="Too many ingredients (max 50)")

    invalid = set(body.dietary) - _VALID_DIETARY
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid dietary filter(s): {sorted(invalid)}")

    from recipe_search import match_recipes

    df = get_df()
    valid_indices = _get_dietary_valid_indices(df, body.dietary)
    results = match_recipes(body.ingredients, df, valid_indices=valid_indices)

    return [_to_recipe_response(r) for r in results]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
