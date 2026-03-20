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


def _pick_col(df: pd.DataFrame, candidates: List[str]) -> str | None:
    for name in candidates:
        if name in df.columns:
            return name
    return None


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
# LOAD & PREPARE DATAFRAME
# -------------------------------------------------
def load_recipes(csv_path: str | Path | None = None) -> pd.DataFrame:
    if csv_path is None:
        csv_path = BASE_DIR.parent / "data" / "raw" / "recipes.csv"

    p = Path(csv_path)
    if not p.is_absolute():
        p = BASE_DIR / p
    if not p.exists():
        for alt in [
            BASE_DIR.parent / "data" / "raw" / "recipes.csv",
            BASE_DIR.parent / "data" / "cleaned" / "recipes.csv",
            BASE_DIR / "recipes.csv",
        ]:
            if alt.exists():
                p = alt
                break

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

    if "img_src" in df.columns:
        out["img_src"] = df["img_src"].fillna("").astype(str)
    else:
        out["img_src"] = ""

    # Nutrition parsing
    if "nutrition" in df.columns:
        out["calories"] = df["nutrition"].apply(_extract_calories)
        out["protein_g"] = df["nutrition"].apply(lambda s: _extract_grams(s, "Protein"))
        out["fat_g"] = df["nutrition"].apply(lambda s: _extract_grams(s, "Total Fat"))
        out["fiber_g"] = df["nutrition"].apply(lambda s: _extract_grams(s, "Dietary Fiber"))
        out["sugar_g"] = df["nutrition"].apply(lambda s: _extract_grams(s, "Total Sugars"))
        out["carbs_g"] = df["nutrition"].apply(lambda s: _extract_grams(s, "Total Carbohydrate"))
    else:
        for col in ["calories", "protein_g", "fat_g", "fiber_g", "sugar_g", "carbs_g"]:
            out[col] = 0.0

    # Cook time and servings
    if "cook_time" in df.columns:
        out["cook_time"] = df["cook_time"].fillna("").astype(str)
    else:
        out["cook_time"] = ""

    if "servings" in df.columns:
        out["servings"] = df["servings"].fillna("").astype(str)
    else:
        out["servings"] = ""

    return out


# -------------------------------------------------
# HEALTH SCORE LOGIC
# -------------------------------------------------
def _compute_health_score(row: pd.Series) -> float:
    protein = float(row.get("protein_g", 0.0) or 0.0)
    fat = float(row.get("fat_g", 0.0) or 0.0)
    sugar = float(row.get("sugar_g", 0.0) or 0.0)
    carbs = float(row.get("carbs_g", 0.0) or 0.0)
    net_carbs = max(carbs, 0.0)

    PROTEIN_TARGET = 20.0
    FAT_LIMIT = 25.0
    SUGAR_LIMIT = 40.0
    NET_CARBS_LIMIT = 120.0

    protein_score = min(protein / PROTEIN_TARGET, 1.0)
    fat_score = 1.0 - min(fat / FAT_LIMIT, 1.0)
    sugar_score = 1.0 - min(sugar / SUGAR_LIMIT, 1.0)
    net_carbs_score = 1.0 - min(net_carbs / NET_CARBS_LIMIT, 1.0)

    health = (
        0.40 * protein_score +
        0.25 * fat_score +
        0.20 * sugar_score +
        0.15 * net_carbs_score
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
    quota: int = 7,
    hi_thresh: float = 0.5,
    lo_thresh: float = 0.3,
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

    candidates: List[Dict] = []

    for idx, row in df.iterrows():
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

        pct_recipe = matches / recipe_size if recipe_size > 0 else 0.0
        pct_user = matches / len(user_cores) if user_cores else 0.0
        union_size = len(user_cores | recipe_set)
        jaccard = matches / union_size if union_size > 0 else 0.0
        match_score = 0.7 * pct_recipe + 0.3 * jaccard
        health_score = _compute_health_score(row)

        # Parse servings as integer if possible
        servings_raw = str(row.get("servings", "") or "")
        servings_int = None
        m = re.search(r"(\d+)", servings_raw)
        if m:
            try:
                servings_int = int(m.group(1))
            except ValueError:
                pass

        candidates.append({
            "id":             int(idx),
            "name":           row["display_name"],
            "matches":        matches,
            "pct_recipe":     pct_recipe,
            "pct_user":       pct_user,
            "score":          match_score,
            "jaccard":        jaccard,
            "recipe_size":    recipe_size,
            "health_score":   health_score,
            "protein_g":      float(row.get("protein_g", 0.0) or 0.0),
            "fat_g":          float(row.get("fat_g", 0.0) or 0.0),
            "sugar_g":        float(row.get("sugar_g", 0.0) or 0.0),
            "carbs_g":        float(row.get("carbs_g", 0.0) or 0.0),
            "calories":       int(row.get("calories", 0) or 0),
            "cook_time":      str(row.get("cook_time", "") or ""),
            "servings":       servings_int,
            "url":            str(row.get("url", "") or ""),
            "img_src":        str(row.get("img_src", "") or ""),
            "matched_cores":  sorted(matched_ingredients),
            "user_cores":     sorted(user_cores),
        })

    if not candidates:
        return []

    candidates.sort(key=lambda c: (-c["score"], c["recipe_size"]))
    return candidates[:quota]
