# backend/recipe_search.py
from __future__ import annotations
from ast import literal_eval
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Set
import heapq
import logging
import re
import pandas as pd
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)


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
    "fresh", "extra", "extra-virgin",
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
    text = _FRAC_RE.sub(" ", text)
    text = _DIGIT_RE.sub(" ", text)
    return text


MEAT_TOKENS = {
    "chicken", "beef", "pork", "lamb", "goat", "turkey",
    "duck", "goose", "fish", "salmon", "tilapia", "tuna",
    "shrimp", "prawn", "prawns", "scallops", "bacon",
    "sausage", "ham"
}

# -------------------------------------------------
# DIETARY CLASSIFICATION REGEXES
# Applied to joined raw ingredient text at load time.
# -------------------------------------------------
_PLANT_DAIRY_RE = re.compile(
    r'\b(coconut|almond|oat|soy|soya|rice|hemp|cashew)\s+(milk|cream|butter|cheese|yogurt)\b'
    r'|\b(peanut|almond|cashew|sunflower|hazelnut|apple|peach|pumpkin|cocoa|shea)\s+butter\b'
    r'|\bcream\s+of\s+tartar\b'
    r'|\bnon[- ]dairy\s+(milk|cream|butter|cheese|yogurt)\b'
    r'|\bdairy[- ]free\s+(milk|cream|butter|cheese|yogurt)\b',
    re.IGNORECASE,
)
_GF_FLOUR_RE = re.compile(
    r'\b(rice|almond|coconut|chickpea|tapioca|potato|corn|cassava|arrowroot|'
    r'buckwheat|teff|amaranth|sorghum|millet)\s+flour\b'
    r'|\bgluten[- ]free\s+flour\b',
    re.IGNORECASE,
)
_MEAT_SEAFOOD_RE = re.compile(
    r'\b(chicken|beef|pork|lamb|turkey|duck|goose|veal|venison|bison|'
    r'bacon|ham|sausage|pepperoni|salami|prosciutto|pancetta|chorizo|'
    r'fish|salmon|tuna|tilapia|cod|halibut|trout|bass|'
    r'sardines?|shrimps?|prawns?|scallops?|crabs?|lobsters?|oysters?|clams?|'
    r'mussels?|squids?|calamari|anchovy|anchovies|gelatin|lard|suet)\b',
    re.IGNORECASE,
)
_DAIRY_RE = re.compile(
    r'\b(milk|cream|cheese|butter|yogurt|yoghurt|ghee|whey|casein|lactose|buttermilk|'
    r'half-and-half)\b',
    re.IGNORECASE,
)
_EGG_RE = re.compile(r'\beggs?\b', re.IGNORECASE)
_HONEY_RE = re.compile(r'\bhoney\b', re.IGNORECASE)
_GLUTEN_RE = re.compile(
    r'\b(wheat|flour|barley|rye|spelt|farro|bulgur|semolina|seitan|malt|triticale|'
    r'couscous|pasta|noodles?|udon|ramen|bread|breadcrumbs?|panko|pita|cracker|crouton|oats?)\b'
    r'|\bsoy\s+sauce\b',
    re.IGNORECASE,
)


def _clean_ingredient_to_core(ing: str) -> str:
    if not isinstance(ing, str):
        return ""

    ing = ing.lower()
    ing = _remove_numbers(ing)
    ing = _NON_WORD_RE.sub(" ", ing)
    ing = _SPACES_RE.sub(" ", ing).strip()

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


_FRAC_RE = re.compile(r"\d+\/\d+")
_DIGIT_RE = re.compile(r"\d+")
_NON_WORD_RE = re.compile(r"[^\w\s]")
_SPACES_RE = re.compile(r"\s+")

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
        logger.info("Downloading recipes.csv from HuggingFace...")
        path.parent.mkdir(parents=True, exist_ok=True)
        hf_hub_download(
            repo_id=_RECIPES_HF_REPO,
            filename="recipes.csv",
            repo_type="dataset",
            local_dir=str(path.parent),
        )
        logger.info("Downloaded recipes.csv")
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
        mins = int(m.group(2)) if m.group(2) else 0
        if hours >= 24:
            days = hours // 24
            remaining = hours % 24
            label = f"{days} day{'s' if days != 1 else ''}"
            parts = [label]
            if remaining:
                parts.append(f"{remaining} hr")
            if mins:
                parts.append(f"{mins} min")
            return " ".join(parts)
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

    def parse_ings_raw(x):
        if not isinstance(x, str):
            return []
        x = x.strip()
        if x.startswith("[") and x.endswith("]"):
            try:
                val = literal_eval(x)
                if isinstance(val, list):
                    return [str(item).strip() for item in val if str(item).strip()]
            except Exception:
                pass
        return [part.strip() for part in x.split(",") if part.strip()]

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
    out["ingredients_raw"] = df["ingredients"].apply(parse_ings_raw)

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
    out["display_name_lower"] = out["display_name"].str.lower()

    _ing_text = out["ingredients_raw"].str.join(" ")
    _ing_no_plant_dairy = _ing_text.str.replace(_PLANT_DAIRY_RE, " ", regex=True)
    _ing_no_gf_flour    = _ing_text.str.replace(_GF_FLOUR_RE, " ", regex=True)

    out["is_vegetarian"]  = ~_ing_text.str.contains(_MEAT_SEAFOOD_RE, regex=True)
    _has_dairy            = _ing_no_plant_dairy.str.contains(_DAIRY_RE, regex=True)
    _has_egg              = _ing_text.str.contains(_EGG_RE, regex=True)
    _has_honey            = _ing_text.str.contains(_HONEY_RE, regex=True)
    out["is_vegan"]       = out["is_vegetarian"] & ~_has_dairy & ~_has_egg & ~_has_honey
    out["is_gluten_free"] = ~_ing_no_gf_flour.str.contains(_GLUTEN_RE, regex=True)

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


def _dietary_flags(idx, veg_arr, vegan_arr, gf_arr) -> List[str]:
    flags: List[str] = []
    if veg_arr is not None and veg_arr[idx]:
        flags.append("vegetarian")
    if vegan_arr is not None and vegan_arr[idx]:
        flags.append("vegan")
    if gf_arr is not None and gf_arr[idx]:
        flags.append("gluten_free")
    return flags


# -------------------------------------------------
# MATCHING LOGIC
# -------------------------------------------------
@lru_cache(maxsize=2048)
def _candidates_for_core(user_core: str) -> frozenset[int]:
    vocab_matches = process.extract(
        user_core,
        _ingredient_vocab_list,
        scorer=fuzz.ratio,
        score_cutoff=82,
        limit=None,
    )
    candidates: set[int] = set()
    for key, _score, _i in vocab_matches:
        candidates.update(_inverted_index[key])
    return frozenset(candidates)


def _get_ingredient_candidates(user_cores: set[str]) -> set[int]:
    """Row indices whose ingredients fuzzy-match any of user_cores."""
    if not user_cores or not _inverted_index or not _ingredient_vocab_list:
        return set()
    candidates: set[int] = set()
    for user_core in user_cores:
        candidates |= _candidates_for_core(user_core)
    return candidates


def match_recipes(
    user_ings: List[str],
    df: pd.DataFrame,
    quota: int = 50,
    valid_indices: set | None = None,
) -> List[Dict]:
    if not user_ings:
        return []

    user_cores = _get_user_cores(user_ings)

    if not user_cores:
        return []

    _build_inverted_index(df)
    candidate_indices = _get_ingredient_candidates(user_cores)
    if valid_indices is not None:
        candidate_indices = candidate_indices & valid_indices

    if not candidate_indices:
        return []

    # Pre-extract columns as numpy arrays — much faster than iterrows()
    names        = df["display_name"].values
    ing_norms    = df["ingredients_norm"].values
    health_arr   = df["health_score"].values
    protein_arr  = df["protein_g"].values
    fat_arr      = df["fat_g"].values
    sugar_arr    = df["sugar_g"].values
    carbs_arr    = df["carbs_g"].values
    calories_arr = df["calories"].values
    cooktime_arr = df["cook_time"].values
    url_arr      = df["url"].values
    ing_raw_arr  = df["ingredients_raw"].values
    veg_arr      = df["is_vegetarian"].values if "is_vegetarian" in df.columns else None
    vegan_arr    = df["is_vegan"].values      if "is_vegan"      in df.columns else None
    gf_arr       = df["is_gluten_free"].values if "is_gluten_free" in df.columns else None

    candidates: List[Dict] = []

    for idx in candidate_indices:
        recipe_cores = ing_norms[idx]
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
        n_matches = len(matched_ingredients)

        if n_matches == 0:
            continue

        pct_recipe  = n_matches / recipe_size
        pct_user    = n_matches / len(user_cores)
        union_size  = len(user_cores | recipe_set)
        jaccard     = n_matches / union_size if union_size > 0 else 0.0
        match_score = _compute_match_score(pct_recipe, pct_user, jaccard)

        candidates.append({
            "id":            int(idx),
            "name":          str(names[idx]),
            "matches":       n_matches,
            "pct_recipe":    pct_recipe,
            "pct_user":      pct_user,
            "score":         match_score,
            "jaccard":       jaccard,
            "recipe_size":   recipe_size,
            "health_score":  float(health_arr[idx]),
            "protein_g":     float(protein_arr[idx]),
            "fat_g":         float(fat_arr[idx]),
            "sugar_g":       float(sugar_arr[idx]),
            "carbs_g":       float(carbs_arr[idx]),
            "calories":      int(calories_arr[idx]),
            "cook_time":     str(cooktime_arr[idx]),
            "url":           str(url_arr[idx]),
            "ingredients_raw": list(ing_raw_arr[idx]),
            "matched_cores": matched_ingredients,
            "dietary_flags": _dietary_flags(idx, veg_arr, vegan_arr, gf_arr),
        })

    if not candidates:
        return []

    top = heapq.nlargest(quota, candidates, key=lambda c: (c["score"], -c["recipe_size"]))
    for r in top:
        matched_cores = r.pop("matched_cores")
        missing_raw: list[str] = []
        seen: set[str] = set()
        for raw_ing in r["ingredients_raw"]:
            core = _clean_ingredient_to_core(raw_ing)
            if not core or core in matched_cores or core in seen:
                continue
            seen.add(core)
            missing_raw.append(raw_ing)
        r["missing_raw"] = missing_raw
    return top


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


@lru_cache(maxsize=4096)
def _correct_cached(core: str, threshold: float) -> tuple[str, bool] | None:
    if core in _ingredient_vocab:
        return (core.title(), True)
    match = process.extractOne(core, _ingredient_vocab_list, scorer=fuzz.ratio, score_cutoff=threshold * 100)
    if match:
        return (match[0].title(), True)
    return None


def correct_ingredient(user_input: str, df: pd.DataFrame, threshold: float = 0.80) -> tuple[str, bool]:
    core = _clean_ingredient_to_core(user_input)
    if not core:
        return user_input.strip().title(), False
    _build_vocab(df)
    result = _correct_cached(core, threshold)
    return result if result is not None else (user_input.strip().title(), False)


def search_by_name(query: str, df: pd.DataFrame, user_ings: List[str] | None = None, limit: int = 100, valid_indices: set | None = None) -> List[Dict]:
    if not query.strip():
        return []
    q = query.strip().lower()
    mask = df["display_name_lower"].str.contains(q, na=False, regex=False)
    name_indices = set(df.index[mask])

    if not name_indices:
        return []

    user_cores = _get_user_cores(user_ings) if user_ings else set()

    if valid_indices is not None:
        name_indices = name_indices & valid_indices

    if not name_indices:
        return []

    _build_inverted_index(df)
    ingredient_candidates = _get_ingredient_candidates(user_cores)
    match_indices = list(name_indices & ingredient_candidates) if ingredient_candidates else []

    if not match_indices:
        return []

    names        = df["display_name"].values
    ing_norms    = df["ingredients_norm"].values
    health_arr   = df["health_score"].values
    protein_arr  = df["protein_g"].values
    fat_arr      = df["fat_g"].values
    sugar_arr    = df["sugar_g"].values
    carbs_arr    = df["carbs_g"].values
    calories_arr = df["calories"].values
    cooktime_arr = df["cook_time"].values
    url_arr      = df["url"].values
    ing_raw_arr  = df["ingredients_raw"].values
    veg_arr      = df["is_vegetarian"].values if "is_vegetarian" in df.columns else None
    vegan_arr    = df["is_vegan"].values      if "is_vegan"      in df.columns else None
    gf_arr       = df["is_gluten_free"].values if "is_gluten_free" in df.columns else None

    results = []
    for idx in match_indices:
        recipe_set = set(ing_norms[idx])
        recipe_size = len(recipe_set)
        missing_raw: list[str] = []
        if user_cores and recipe_size > 0:
            matched = _fuzzy_intersection(user_cores, recipe_set)
            match_count = len(matched)
            pct_recipe = match_count / recipe_size
            union_size = len(user_cores | recipe_set)
            jaccard = match_count / union_size if union_size > 0 else 0.0
            score = _compute_match_score(pct_recipe, match_count / len(user_cores), jaccard)
            seen_m: set[str] = set()
            for raw_ing in ing_raw_arr[idx]:
                core = _clean_ingredient_to_core(raw_ing)
                if not core or core in matched or core in seen_m:
                    continue
                seen_m.add(core)
                missing_raw.append(raw_ing)
        else:
            match_count = 0
            score = 0.0

        results.append({
            "id":            int(idx),
            "name":          str(names[idx]),
            "matches":       match_count,
            "score":         score,
            "recipe_size":   recipe_size,
            "health_score":  float(health_arr[idx]),
            "protein_g":     float(protein_arr[idx]),
            "fat_g":         float(fat_arr[idx]),
            "sugar_g":       float(sugar_arr[idx]),
            "carbs_g":       float(carbs_arr[idx]),
            "calories":      int(calories_arr[idx]),
            "cook_time":     str(cooktime_arr[idx]),
            "url":           str(url_arr[idx]),
            "ingredients_raw": list(ing_raw_arr[idx]),
            "missing_raw":   missing_raw,
            "dietary_flags": _dietary_flags(idx, veg_arr, vegan_arr, gf_arr),
        })

    results.sort(key=lambda r: -r["score"])
    return results[:limit]
