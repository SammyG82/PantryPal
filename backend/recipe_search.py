# backend/recipe_search.py
from __future__ import annotations
from ast import literal_eval
from pathlib import Path
from typing import List, Dict, Set
import re
import pandas as pd
from rapidfuzz import fuzz, process


# -------------------------------------------------
# PATHS — backend/ as base, data at ../data/raw/recipes.csv
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

# -------------------------------------------------
# INGREDIENT NORMALISATION & CLEANUP
# -------------------------------------------------
ING_STOPWORDS = {
    # preparation methods
    "finely", "thinly", "roughly", "freshly", "lightly",
    "chopped", "sliced", "diced", "minced", "peeled",
    "seeded", "cored", "grated", "crushed", "julienned",
    "halved", "quartered", "cubed", "skinless", "softened",
    "shredded", "beaten", "rinsed", "drained", "mashed",
    "whisked", "stirred", "boneless", "bone-in",

    # quantity / units
    "cup", "cups", "tablespoon", "tablespoons",
    "teaspoon", "teaspoons", "tbsp", "tsp",
    "ounce", "ounces", "oz", "pound", "pounds", "lb", "lbs",
    "gram", "grams", "kg", "kilogram", "kilograms",

    # size
    "large", "small", "medium",

    # quality descriptors
    "fresh", "freshly", "extra", "extra-virgin",
    "low-fat", "fat-free", "reduced", "light",

    # state/preparation
    "dried", "smoked", "roasted", "grilled", "fried", "baked",
    "toasted", "cooked", "raw",

    # connectors
    "and", "or", "with", "without", "of", "in", "for", "to",
    "taste", "divided", "optional", "recipe", "can", "package",

    "salt", "pepper", "peppers", "water",
    "oil", "olive", "olive-oil", "canola", "vegetable",
    "sugar", "flour",
    "broth", "stock",
}


def _normalize(s: str) -> str:
    """Lowercase + trim + collapse inner spaces."""
    return " ".join(s.lower().strip().split())


def _remove_numbers(text: str) -> str:
    """Remove integers and simple fractions like 1/2, 3/4."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"\d+\/\d+", " ", text)
    text = re.sub(r"\d+", " ", text)
    return text


MEAT_TOKENS = {
    "chicken", "beef", "pork", "lamb", "goat", "turkey",
    "duck", "goose", "fish", "salmon", "tilapia", "tuna",
    "shrimp", "prawn", "prawns", "scallops", "bacon",
    "sausage", "ham"
}


def _clean_ingredient_to_core(ing: str) -> str:
    if not isinstance(ing, str):
        return ""

    ing = ing.lower()
    ing = _remove_numbers(ing)
    ing = re.sub(r"[^\w\s]", " ", ing)
    ing = re.sub(r"\s+", " ", ing).strip()

    tokens: List[str] = []
    for tok in ing.split():
        if tok in ING_STOPWORDS:
            continue
        if len(tok) > 2:
            tokens.append(tok)

    if not tokens:
        return ""

    for tok in tokens:
        if tok in MEAT_TOKENS:
            return tok

    last_word = tokens[-1]
    if last_word.endswith("oes"):
        return last_word[:-2]
    elif last_word.endswith("es") and len(last_word) > 4:
        if not last_word.endswith(("eese", "ose")):
            return last_word[:-2]
    elif last_word.endswith("s") and len(last_word) > 3:
        if not last_word.endswith("ss"):
            return last_word[:-1]

    return last_word


def _normalize_list(xs: List[str]) -> List[str]:
    normed = []
    seen = set()
    for x in xs:
        if not isinstance(x, str):
            continue
        nx = _normalize(x)
        if not nx:
            continue
        if nx in seen:
            continue
        seen.add(nx)
        normed.append(nx)
    return normed


_CALORIES_RE = re.compile(r"Calories\s+(\d+)", re.IGNORECASE)
_NUTRITION_RE: dict[str, re.Pattern] = {
    label: re.compile(rf"{re.escape(label)}\s+(\d+(\.\d*)?)g")
    for label in ("Protein", "Total Fat", "Total Sugars", "Total Carbohydrate")
}


def _extract_grams(text: str, label: str) -> float:
    if not isinstance(text, str):
        return 0.0
    m = _NUTRITION_RE[label].search(text)
    if not m:
        return 0.0
    try:
        return float(m.group(1))
    except ValueError:
        return 0.0


def _extract_calories(text: str) -> int:
    if not isinstance(text, str):
        return 0
    m = _CALORIES_RE.search(text)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return 0
    return 0


def _parse_nutrition_row(text: str) -> dict:
    """Parse all nutrition fields from a single nutrition string in one pass."""
    if not isinstance(text, str):
        return {"calories": 0, "protein_g": 0.0, "fat_g": 0.0, "sugar_g": 0.0, "carbs_g": 0.0}
    return {
        "calories": _extract_calories(text),
        "protein_g": _extract_grams(text, "Protein"),
        "fat_g": _extract_grams(text, "Total Fat"),
        "sugar_g": _extract_grams(text, "Total Sugars"),
        "carbs_g": _extract_grams(text, "Total Carbohydrate"),
    }


# -------------------------------------------------
# HUGGINGFACE AUTO-DOWNLOAD
# -------------------------------------------------
_RECIPES_HF_REPO = "SammyG82/pantrypal-data"
_RECIPES_DEFAULT = BASE_DIR.parent / "data" / "raw" / "recipes.csv"


def _ensure_recipes(path: Path) -> None:
    if path.exists():
        return
    try:
        from huggingface_hub import hf_hub_download
        print("Downloading recipes.csv from HuggingFace...")
        path.parent.mkdir(parents=True, exist_ok=True)
        hf_hub_download(
            repo_id=_RECIPES_HF_REPO,
            filename="recipes.csv",
            repo_type="dataset",
            local_dir=str(path.parent),
        )
        print("Downloaded recipes.csv")
    except Exception as e:
        raise RuntimeError(f"recipes.csv not found and download failed: {e}") from e


# -------------------------------------------------
# LOAD & PREPARE DATAFRAME
_HR_RE = re.compile(r"^(\d+)\s*hr(?:\s+(\d+)\s*mins?)?$")


def _normalise_cook_time(raw: str) -> str:
    value = raw.strip()
    if not value or value == "nan":
        return "N/A"
    m = _HR_RE.match(value)
    if m:
        hours = int(m.group(1))
        if hours >= 24:
            days = hours // 24
            remaining = hours % 24
            label = f"{days} day{'s' if days != 1 else ''}"
            return f"{label} {remaining} hr" if remaining else label
    return value


# -------------------------------------------------
def load_recipes(csv_path: str | Path | None = None) -> pd.DataFrame:
    if csv_path is None:
        csv_path = _RECIPES_DEFAULT

    p = Path(csv_path)
    if not p.is_absolute():
        p = BASE_DIR / p
    _ensure_recipes(p)

    df = pd.read_csv(p)

    def parse_ings(x):
        if not isinstance(x, str):
            return []
        x = x.strip()
        core_ingredients: List[str] = []
        if x.startswith("[") and x.endswith("]"):
            try:
                val = literal_eval(x)
                if isinstance(val, list):
                    for item in val:
                        core = _clean_ingredient_to_core(item)
                        if core:
                            core_ingredients.append(core)
                    return _normalize_list(core_ingredients)
            except Exception:
                pass
        parts = [part.strip() for part in x.split(",")]
        for part in parts:
            core = _clean_ingredient_to_core(part)
            if core:
                core_ingredients.append(core)
        return _normalize_list(core_ingredients)

    if "ingredients" not in df.columns:
        raise ValueError("CSV has no 'ingredients' column")

    df["ingredients_norm"] = df["ingredients"].apply(parse_ings)

    name_col = None
    for col in ["recipe_name", "title", "name"]:
        if col in df.columns:
            name_col = col
            break

    if name_col is not None:
        df["display_name"] = df[name_col].fillna("").astype(str)
    else:
        df["display_name"] = df.index.astype(str)

    out = df[["display_name", "ingredients_norm"]].copy()

    if "url" in df.columns:
        out["url"] = df["url"].fillna("").astype(str)
    else:
        out["url"] = ""

    # Nutrition parsing
    if "nutrition" in df.columns:
        nutrition_parsed = pd.DataFrame(df["nutrition"].apply(_parse_nutrition_row).tolist())
        out["calories"] = nutrition_parsed["calories"].values
        out["protein_g"] = nutrition_parsed["protein_g"].values
        out["fat_g"] = nutrition_parsed["fat_g"].values
        out["sugar_g"] = nutrition_parsed["sugar_g"].values
        out["carbs_g"] = nutrition_parsed["carbs_g"].values
    else:
        for col in ["calories", "protein_g", "fat_g", "sugar_g", "carbs_g"]:
            out[col] = 0.0

    if "cook_time" in df.columns:
        out["cook_time"] = df["cook_time"].fillna("").astype(str).apply(_normalise_cook_time)
    else:
        out["cook_time"] = ""

    out["health_score"] = _compute_health_scores_vectorized(out)

    return out


# -------------------------------------------------
# HEALTH SCORE LOGIC
# -------------------------------------------------
def _compute_health_scores_vectorized(df: pd.DataFrame) -> pd.Series:
    """Pre-compute health scores for all rows at once using vectorized operations."""
    protein = df["protein_g"].astype(float).fillna(0.0)
    sugar = df["sugar_g"].astype(float).fillna(0.0)
    calories = df["calories"].astype(float).fillna(0.0)
    return (
        0.45 * (protein / 25.0).clip(0.0, 1.0) +
        0.25 * (1.0 - (sugar / 30.0).clip(0.0, 1.0)) +
        0.30 * (1.0 - (calories / 800.0).clip(0.0, 1.0))
    ).clip(0.0, 1.0)


def _compute_health_score(row: pd.Series) -> float:
    return float(row.get("health_score", 0.0) or 0.0)


def _fuzzy_intersection(
    user_cores: Set[str],
    recipe_cores: Set[str],
    threshold: float = 0.82,
) -> Set[str]:
    if not user_cores or not recipe_cores:
        return set()

    exact = user_cores & recipe_cores
    matches: Set[str] = set(exact)
    remaining_user = user_cores - exact
    remaining_recipe = list(recipe_cores - exact)

    for u in remaining_user:
        if not remaining_recipe:
            break
        result = process.extractOne(
            u,
            remaining_recipe,
            scorer=fuzz.token_set_ratio,
            score_cutoff=threshold * 100,
        )
        if result is not None:
            key, _score, idx = result
            matches.add(key)
            remaining_recipe.pop(idx)

    return matches


# -------------------------------------------------
# SHARED HELPERS
# -------------------------------------------------
def _get_user_cores(user_ings: List[str]) -> Set[str]:
    cores: Set[str] = set()
    for u in user_ings:
        core = _clean_ingredient_to_core(u)
        if core:
            cores.add(core)
    return cores


def _compute_match_score(pct_recipe: float, pct_user: float, jaccard: float) -> float:
    return 0.6 * pct_recipe + 0.25 * pct_user + 0.15 * jaccard


# -------------------------------------------------
# MATCHING LOGIC
# -------------------------------------------------
def match_recipes(
    user_ings: List[str],
    df: pd.DataFrame,
    quota: int = 50,
) -> List[Dict]:
    if not user_ings:
        return []

    user_cores = _get_user_cores(user_ings)

    if not user_cores:
        return []

    inv = _build_inverted_index(df)
    vocab_list = _ingredient_vocab_list
    candidate_indices: set[int] = set()
    for user_core in user_cores:
        matches = process.extract(
            user_core,
            vocab_list,
            scorer=fuzz.ratio,
            score_cutoff=82,
            limit=None,
        )
        for key, _score, _i in matches:
            candidate_indices.update(inv[key])

    if not candidate_indices:
        return []

    candidates: List[Dict] = []
    candidates_batch = df.iloc[sorted(candidate_indices)]

    for global_idx, row in candidates_batch.iterrows():
        recipe_cores = row["ingredients_norm"]
        if not recipe_cores:
            continue

        recipe_set = set(recipe_cores)
        recipe_size = len(recipe_set)

        if recipe_size <= 1:
            continue

        matched_ingredients = _fuzzy_intersection(
            user_cores=user_cores,
            recipe_cores=recipe_set,
            threshold=0.82,
        )
        matches = len(matched_ingredients)

        if matches == 0:
            continue

        pct_recipe = matches / recipe_size
        pct_user = matches / len(user_cores)
        union_size = len(user_cores | recipe_set)
        jaccard = matches / union_size if union_size > 0 else 0.0
        match_score = _compute_match_score(pct_recipe, pct_user, jaccard)
        health_score = _compute_health_score(row)

        candidates.append({
            "id":           int(global_idx),
            "name":         row["display_name"],
            "matches":      matches,
            "pct_recipe":   pct_recipe,
            "pct_user":     pct_user,
            "score":        match_score,
            "jaccard":      jaccard,
            "recipe_size":  recipe_size,
            "health_score": health_score,
            "protein_g":    float(row.get("protein_g", 0.0) or 0.0),
            "fat_g":        float(row.get("fat_g", 0.0) or 0.0),
            "sugar_g":      float(row.get("sugar_g", 0.0) or 0.0),
            "carbs_g":      float(row.get("carbs_g", 0.0) or 0.0),
            "calories":     int(row.get("calories", 0) or 0),
            "cook_time":    str(row.get("cook_time", "") or ""),
            "url":          str(row.get("url", "") or ""),
        })

    if not candidates:
        return []

    candidates.sort(key=lambda c: (-c["score"], c["recipe_size"]))
    return candidates[:quota]


_ingredient_vocab: set[str] | None = None
_ingredient_vocab_list: list[str] | None = None
_inverted_index: dict[str, list[int]] | None = None


def _build_inverted_index(df: pd.DataFrame) -> dict[str, list[int]]:
    global _inverted_index, _ingredient_vocab, _ingredient_vocab_list
    if _inverted_index is None:
        idx: dict[str, list[int]] = {}
        for i, cores in enumerate(df["ingredients_norm"]):
            for core in cores:
                idx.setdefault(core, []).append(i)
        _inverted_index = idx
        if _ingredient_vocab is None:
            _ingredient_vocab = set(idx.keys())
        if _ingredient_vocab_list is None:
            _ingredient_vocab_list = list(idx.keys())
    return _inverted_index


def _build_vocab(df: pd.DataFrame) -> set[str]:
    _build_inverted_index(df)  # builds vocab as a side effect
    return _ingredient_vocab  # type: ignore[return-value]


_correction_cache: dict[str, tuple[str, bool]] = {}


def correct_ingredient(user_input: str, df: pd.DataFrame, threshold: float = 0.80) -> tuple[str, bool]:
    cache_key = user_input.lower().strip()
    if cache_key in _correction_cache:
        return _correction_cache[cache_key]

    core = _clean_ingredient_to_core(user_input)
    if not core:
        result = user_input.strip().title(), False
        _correction_cache[cache_key] = result
        return result

    vocab = _build_vocab(df)
    if not vocab:
        result = user_input.strip().title(), False
        _correction_cache[cache_key] = result
        return result

    if core in vocab:
        result = core.title(), True
        _correction_cache[cache_key] = result
        return result

    best_match = None
    best_score = 0.0
    for candidate in vocab:
        score = fuzz.ratio(core, candidate) / 100.0
        if score > best_score:
            best_score = score
            best_match = candidate

    result = (best_match.title(), True) if (best_match and best_score >= threshold) else (user_input.strip().title(), False)
    _correction_cache[cache_key] = result
    return result


def search_by_name(query: str, df: pd.DataFrame, user_ings: List[str] | None = None, limit: int = 20) -> List[Dict]:
    if not query.strip():
        return []
    q = query.strip().lower()
    mask = df["display_name"].str.lower().str.contains(q, na=False)
    matches = df[mask].head(limit)

    user_cores = _get_user_cores(user_ings) if user_ings else set()

    results = []
    for idx, row in matches.iterrows():
        health_score = _compute_health_score(row)
        cook_time_raw = str(row.get("cook_time", "") or "")

        recipe_set = set(row["ingredients_norm"])
        recipe_size = len(recipe_set)
        if user_cores and recipe_size > 0:
            matched = _fuzzy_intersection(user_cores, recipe_set)
            match_count = len(matched)
            pct_recipe = match_count / recipe_size
            union_size = len(user_cores | recipe_set)
            jaccard = match_count / union_size if union_size > 0 else 0.0
            score = _compute_match_score(pct_recipe, match_count / len(user_cores), jaccard)
        else:
            match_count = 0
            score = 0.0

        results.append({
            "id":           int(idx),
            "name":         row["display_name"],
            "matches":      match_count,
            "score":        score,
            "recipe_size":  recipe_size,
            "health_score": health_score,
            "protein_g":    float(row.get("protein_g", 0.0) or 0.0),
            "fat_g":        float(row.get("fat_g", 0.0) or 0.0),
            "sugar_g":      float(row.get("sugar_g", 0.0) or 0.0),
            "carbs_g":      float(row.get("carbs_g", 0.0) or 0.0),
            "calories":     int(row.get("calories", 0) or 0),
            "cook_time":    cook_time_raw,
            "url":          str(row.get("url", "") or ""),
        })
    return results
