# backend/app.py
from __future__ import annotations

import asyncio
import io
import logging
import struct
import threading
import time
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
    b'BM',                 # BMP
    b'II*\x00',            # TIFF LE
    b'MM\x00*',            # TIFF BE
)


def _is_valid_image(contents: bytes) -> bool:
    if any(contents.startswith(m) for m in _IMAGE_MAGIC):
        return True
    # WebP: bytes 0–3 are RIFF, bytes 8–11 are WEBP
    return contents[:4] == b'RIFF' and contents[8:12] == b'WEBP'

# -------------------------------------------------
# App setup
# -------------------------------------------------
class _DependencyLoadError(RuntimeError):
    """Raised when a dependency (recipe data or model) failed its most recent
    load attempt. Distinct from TimeoutError (still loading). A failure here
    triggers one background retry (see _ManagedDependency.retry) rather than
    503ing permanently — the retry lock ensures only one reload attempt runs
    at a time regardless of how many requests observe the failure."""


# How long a request waits on a stuck/in-progress load (e.g. a stalled
# download) before failing with a 503 instead of hanging forever. Sized for
# a real cold start: downloading the CLIP weights + model files + the full
# recipe CSV, then parsing/vectorizing 231k rows, can comfortably exceed a
# minute on a free-tier container.
_WARMUP_WAIT_TIMEOUT = 180

# Minimum time between automatic retry attempts for a persistently failing
# dependency — without this, every request during an outage (e.g. HF Hub
# unreachable) would immediately re-trigger a full reload the instant the
# previous attempt finished. Measured from when an attempt *finishes*
# (stamped in _ManagedDependency.load's `finally`), not when it starts —
# otherwise a slow failure (e.g. a stalled download taking longer than the
# cooldown itself) would provide no throttling at all.
_RETRY_COOLDOWN = 30


class _ManagedDependency:
    """Lazy-loads a heavy dependency (recipe data or model) off the event
    loop, with a single-retry-at-a-time self-heal on failure. `loader` is a
    zero-arg callable that performs the load and returns the loaded value
    (or raises)."""

    def __init__(self, name: str, loader):
        self.name = name
        self._loader = loader
        self.value = None
        self.ready = threading.Event()
        self.failed = False
        self._retry_lock = threading.Lock()
        self._last_attempt = 0.0

    def load(self) -> None:
        """Performs the actual load. Called once by the warm-up thread, and
        again by `retry` if that attempt failed — `_retry_lock` ensures only
        one load runs at a time, so this is never racing itself."""
        self.ready.clear()
        try:
            self.value = self._loader()
            self.failed = False
        except Exception:
            self.failed = True
            raise
        finally:
            self._last_attempt = time.monotonic()
            self.ready.set()

    def retry(self) -> bool:
        """Kicks off one background retry after a failed load, so a
        transient failure (e.g. a flaky HF Hub download) self-heals instead
        of 503ing for the rest of the process's life. Returns whether a
        retry was actually scheduled — False if one's already in flight, or
        the last attempt was too recent (_RETRY_COOLDOWN) — so callers can
        report accurately instead of always claiming "retrying"."""
        if time.monotonic() - self._last_attempt < _RETRY_COOLDOWN:
            return False
        if not self._retry_lock.acquire(blocking=False):
            return False

        def _run():
            try:
                self.load()
            except Exception:
                logger.exception(f"Retry failed to load {self.name}")
            finally:
                self._retry_lock.release()

        try:
            threading.Thread(target=_run, daemon=True, name=f"{self.name}-retry").start()
        except Exception:
            self._retry_lock.release()
            logger.exception(f"Failed to start retry thread for {self.name}")
            return False
        return True

    def get(self, timeout: float):
        """Blocks until the current load attempt finishes or `timeout`
        elapses. Never performs the load itself — the warm-up/retry threads
        are the only loaders — so the timeout always bounds the actual
        wait, not a lock acquisition."""
        if not self.ready.wait(timeout=timeout):
            raise TimeoutError(f"{self.name} is still loading")
        if self.failed:
            raise _DependencyLoadError(f"{self.name} failed to load; see server logs")
        return self.value


def _load_df_value():
    from recipe_search import load_recipes, _build_inverted_index
    df = load_recipes()
    _build_inverted_index(df)
    return df


def _load_predictor_value():
    from utils.image_predict import predict_image, load_model
    load_model()
    return predict_image


_df_dep = _ManagedDependency("recipe data", _load_df_value)
_predictor_dep = _ManagedDependency("model", _load_predictor_value)


def _warm_up() -> None:
    """Loads recipe data and the model off the event loop thread, in
    parallel, so the server can accept requests (and pass the platform
    health check) immediately instead of blocking for the full load time.
    Loading them on separate threads means a slow df load can't block the
    predictor (or vice versa) from becoming ready."""
    def _run(dep: _ManagedDependency):
        try:
            dep.load()
        except Exception:
            logger.exception(f"Warm-up failed to load {dep.name}")

    threads = [
        threading.Thread(target=_run, args=(dep,), daemon=True, name=f"warmup-{dep.name}")
        for dep in (_df_dep, _predictor_dep)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if not _df_dep.failed and not _predictor_dep.failed:
        logger.info("Warm-up complete: recipe data and model loaded")


@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=_warm_up, daemon=True, name="warmup").start()
    yield


app = FastAPI(title="PantryPal API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _await_ready(ready_event: threading.Event, timeout: float) -> None:
    """Waits for `ready_event` without tying up a thread-pool worker for the
    whole wait. Routes backed by this call away from a blocking
    `Event.wait()` on a worker thread (anyio's default pool has limited
    capacity, e.g. 40) so a slow warm-up/retry can't exhaust it under
    concurrent requests. Polling via asyncio.sleep costs nothing extra since
    this app serves one container with low concurrency."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not ready_event.is_set():
        if loop.time() >= deadline:
            raise TimeoutError("Still loading")
        await asyncio.sleep(0.25)


async def _get_or_503(dep: _ManagedDependency):
    try:
        await _await_ready(dep.ready, _WARMUP_WAIT_TIMEOUT)
        return dep.get(timeout=0)
    except TimeoutError:
        raise HTTPException(status_code=503, detail="Server is still starting up, try again shortly")
    except _DependencyLoadError:
        retried = dep.retry()
        suffix = ", retrying" if retried else ""
        label = dep.name[0].upper() + dep.name[1:]
        raise HTTPException(status_code=503, detail=f"{label} failed to load{suffix} — try again shortly")


# -------------------------------------------------
# Request / Response models
# -------------------------------------------------
_Ingredient = Annotated[str, StringConstraints(min_length=1, max_length=200, strip_whitespace=True)]

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
async def root():
    return {"message": "PantryPal API is running"}


@app.get("/health")
async def health():
    # Recipe data backs nearly everything (/api/search, /api/recipes,
    # /api/correct), while the model only backs /api/detect — so a failed
    # model load is reported as "degraded" (search still works), not lumped
    # into the same "error" status as a failed data load. Order matters:
    # "degraded" is only accurate once df has actually finished loading —
    # checking df's readiness first keeps a still-loading df from being
    # reported as "degraded" (which would wrongly imply search already
    # works).
    # Checking *.ready.is_set() rather than *.failed directly matters too:
    # _ManagedDependency.load clears the ready event for the duration of
    # every attempt, including retries, while .failed still holds the
    # previous (failed) outcome until that attempt finishes. Reading
    # .failed without the readiness check would report "error"/"degraded"
    # for the whole duration of a retry that's actively in progress and may
    # be about to succeed, instead of "loading".
    # Since df loads independently of (and in parallel with) the predictor,
    # df can finish — and search already be usable — while the predictor is
    # still loading; that gets its own "partially_ready" status rather than
    # being lumped into the generic startup "loading" state.
    if not _df_dep.ready.is_set():
        return {"status": "loading"}
    if _df_dep.failed:
        return {"status": "error", "detail": "recipe data failed to load — check server logs"}
    if not _predictor_dep.ready.is_set():
        return {"status": "partially_ready", "detail": "recipe search ready, model still loading"}
    if _predictor_dep.failed:
        return {"status": "degraded", "detail": "model failed to load — image detection unavailable, check server logs"}
    return {"status": "ready"}


@app.post("/api/detect", response_model=DetectResponse)
async def detect_ingredients(file: UploadFile = File(...)):
    """
    Accept a multipart image upload, run the CNN, return detected ingredient(s).
    """
    if not file.content_type or not file.content_type.lower().startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        contents = await file.read(10 * 1024 * 1024 + 1)
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
        if not _is_valid_image(contents):
            raise HTTPException(status_code=400, detail="File must be a valid image")
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except HTTPException:
        raise
    except (OSError, ValueError, struct.error):
        logger.warning("Image decode failed", exc_info=True)
        raise HTTPException(status_code=400, detail="Could not read image")
    except Exception:
        logger.exception("Unexpected error reading image")
        raise HTTPException(status_code=500, detail="Server error processing image")

    try:
        predict_fn = await _get_or_503(_predictor_dep)
        label = await asyncio.to_thread(predict_fn, image)
        ingredients = [label] if label else []
    except HTTPException:
        raise
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
async def correct_ingredient_endpoint(body: CorrectRequest):
    from recipe_search import correct_ingredient
    df = await _get_or_503(_df_dep)
    corrected, found = await asyncio.to_thread(correct_ingredient, body.ingredient, df)
    return CorrectResponse(corrected=corrected, found=found)


@app.post("/api/search", response_model=List[RecipeResponse])
async def search_recipes(body: SearchRequest):
    if not body.q.strip():
        return []

    invalid = set(body.dietary) - _VALID_DIETARY
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid dietary filter(s): {sorted(invalid)}")

    from recipe_search import search_by_name

    df = await _get_or_503(_df_dep)

    def _run():
        valid_indices = _get_dietary_valid_indices(df, body.dietary)
        return search_by_name(body.q, df, user_ings=body.ingredients or None, valid_indices=valid_indices)

    results = await asyncio.to_thread(_run)

    return [_to_recipe_response(r) for r in results]


@app.post("/api/recipes", response_model=List[RecipeResponse])
async def get_recipes(body: RecipesRequest):
    if not body.ingredients:
        raise HTTPException(status_code=400, detail="No ingredients provided")
    if len(body.ingredients) > 50:
        raise HTTPException(status_code=400, detail="Too many ingredients (max 50)")

    invalid = set(body.dietary) - _VALID_DIETARY
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid dietary filter(s): {sorted(invalid)}")

    from recipe_search import match_recipes

    df = await _get_or_503(_df_dep)

    def _run():
        valid_indices = _get_dietary_valid_indices(df, body.dietary)
        return match_recipes(body.ingredients, df, valid_indices=valid_indices)

    results = await asyncio.to_thread(_run)

    return [_to_recipe_response(r) for r in results]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
