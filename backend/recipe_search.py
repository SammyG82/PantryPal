# backend/recipe_search.py
from __future__ import annotations
from ast import literal_eval
from pathlib import Path
from typing import List, Dict, Set
import re
import pandas as pd
from rapidfuzz import fuzz


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


def _extract_grams(text: str, label: str) -> float:
    if not isinstance(text, str):
        return 0.0
    pattern = rf"{re.escape(label)}\s+(\d+(\.\d*)?)g"
    m = re.search(pattern, text)
    if not m:
        return 0.0
    try:
        return float(m.group(1))
    except ValueError:
        return 0.0


def _extract_calories(text: str) -> int:
    """Extract calories from nutrition string. Looks for 'Calories NNN' pattern."""
    if not isinstance(text, str):
        return 0
    m = re.search(r"Calories\s+(\d+)", text, re.IGNORECASE)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return 0
    return 0


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
        out["calories"] = df["nutrition"].apply(_extract_calories)
        out["protein_g"] = df["nutrition"].apply(lambda s: _extract_grams(s, "Protein"))
        out["fat_g"] = df["nutrition"].apply(lambda s: _extract_grams(s, "Total Fat"))
        out["sugar_g"] = df["nutrition"].apply(lambda s: _extract_grams(s, "Total Sugars"))
        out["carbs_g"] = df["nutrition"].apply(lambda s: _extract_grams(s, "Total Carbohydrate"))
    else:
        for col in ["calories", "protein_g", "fat_g", "sugar_g", "carbs_g"]:
            out[col] = 0.0

    if "cook_time" in df.columns:
        out["cook_time"] = df["cook_time"].fillna("").astype(str)
    else:
        out["cook_time"] = ""

    return out


# -------------------------------------------------
# HEALTH SCORE LOGIC
# -------------------------------------------------
def _compute_health_score(row: pd.Series) -> float:
    protein = float(row.get("protein_g", 0.0) or 0.0)
    sugar = float(row.get("sugar_g", 0.0) or 0.0)
    calories = float(row.get("calories", 0) or 0)

    PROTEIN_TARGET = 25.0
    SUGAR_LIMIT = 30.0
    CALORIE_LIMIT = 800.0

    protein_score = min(protein / PROTEIN_TARGET, 1.0)
    sugar_score = 1.0 - min(sugar / SUGAR_LIMIT, 1.0)
    calorie_score = 1.0 - min(calories / CALORIE_LIMIT, 1.0)

    health = (
        0.45 * protein_score +
        0.25 * sugar_score +
        0.30 * calorie_score
    )
    return float(max(0.0, min(1.0, health)))


def _fuzzy_intersection(
    user_cores: Set[str],
    recipe_cores: Set[str],
    threshold: float = 0.82,
) -> Set[str]:
    if not user_cores or not recipe_cores:
        return set()

    recipe_set: Set[str] = set(recipe_cores)
    exact = user_cores & recipe_set
    matches: Set[str] = set(exact)
    used_recipe: Set[str] = set(exact)

    remaining_user = user_cores - exact
    remaining_recipe = recipe_set - used_recipe

    for u in remaining_user:
        best_r = None
        best_score = 0.0
        for r in list(remaining_recipe):
            score = fuzz.token_set_ratio(u, r) / 100.0
            if score > best_score:
                best_score = score
                best_r = r
        if best_r is not None and best_score >= threshold:
            matches.add(best_r)
            remaining_recipe.remove(best_r)

    return matches


# -------------------------------------------------
# MATCHING LOGIC
# -------------------------------------------------
def match_recipes(
    user_ings: List[str],
    df: pd.DataFrame,
    quota: int = 9,
) -> List[Dict]:
    if not user_ings:
        return []

    user_cores: Set[str] = set()
    for u in user_ings:
        core = _clean_ingredient_to_core(u)
        if core:
            user_cores.add(core)

    if not user_cores:
        return []

    # Use inverted index to find candidate recipes without scanning all rows
    inv = _build_inverted_index(df)
    candidate_indices: set[int] = set()
    for user_core in user_cores:
        for key, row_indices in inv.items():
            if user_core == key or fuzz.ratio(user_core, key) / 100.0 >= 0.82:
                candidate_indices.update(row_indices)

    if not candidate_indices:
        return []

    candidates: List[Dict] = []

    for idx in candidate_indices:
        row = df.iloc[idx]
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
        match_score = 0.6 * pct_recipe + 0.25 * pct_user + 0.15 * jaccard
        health_score = _compute_health_score(row)

        candidates.append({
            "id":           int(idx),
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
_inverted_index: dict[str, list[int]] | None = None


def _build_inverted_index(df: pd.DataFrame) -> dict[str, list[int]]:
    global _inverted_index, _ingredient_vocab
    if _inverted_index is None:
        idx: dict[str, list[int]] = {}
        for i, cores in enumerate(df["ingredients_norm"]):
            for core in cores:
                idx.setdefault(core, []).append(i)
        _inverted_index = idx
        if _ingredient_vocab is None:
            _ingredient_vocab = set(idx.keys())
    return _inverted_index


def _build_vocab(df: pd.DataFrame) -> set[str]:
    _build_inverted_index(df)  # builds vocab as a side effect
    return _ingredient_vocab  # type: ignore[return-value]


def correct_ingredient(user_input: str, df: pd.DataFrame, threshold: float = 0.80) -> tuple[str, bool]:
    core = _clean_ingredient_to_core(user_input)
    if not core:
        return user_input.strip().title(), False

    vocab = _build_vocab(df)
    if not vocab:
        return user_input.strip().title(), False

    if core in vocab:
        return core.title(), True

    best_match = None
    best_score = 0.0
    for candidate in vocab:
        score = fuzz.ratio(core, candidate) / 100.0
        if score > best_score:
            best_score = score
            best_match = candidate

    if best_match and best_score >= threshold:
        return best_match.title(), True

    return user_input.strip().title(), False


def search_by_name(query: str, df: pd.DataFrame, user_ings: List[str] | None = None, limit: int = 20) -> List[Dict]:
    if not query.strip():
        return []
    q = query.strip().lower()
    mask = df["display_name"].str.lower().str.contains(q, na=False)
    matches = df[mask].head(limit)

    user_cores: Set[str] = set()
    if user_ings:
        for u in user_ings:
            core = _clean_ingredient_to_core(u)
            if core:
                user_cores.add(core)

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
            score = 0.6 * pct_recipe + 0.25 * (match_count / len(user_cores)) + 0.15 * jaccard
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
