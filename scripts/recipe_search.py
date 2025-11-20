# # scripts/recipe_search.py
# from __future__ import annotations
# import pandas as pd
# from ast import literal_eval
# from typing import List, Tuple
# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parents[1]

# def _normalize(s: str) -> str:
#     return " ".join(s.lower().strip().split())

# def _normalize_list(xs: List[str]) -> List[str]:
#     return [_normalize(x) for x in xs if isinstance(x, str) and x.strip()]

# def load_recipes(csv_path: str | Path = "data/raw/recipes.csv") -> pd.DataFrame:
#     """
#     Loads a Kaggle 'recipe-ingredients-dataset' style CSV.

#     For your file, we expect columns:
#       - 'ingredients' (a long string: "3 tbsp butter, 2 apples, ...")
#       - 'recipe_name' (used as display name)
#     """
#     p = Path(csv_path)

#     # 🔹 Make relative paths relative to project root (PantryPal/)
#     if not p.is_absolute():
#         p = BASE_DIR / p

#     if not p.exists():
#         # handy fallbacks if you move the file later
#         for rel in [
#             "data/raw/recipes.csv",
#             "data/cleaned/recipes.csv",
#             "recipes.csv",
#         ]:
#             alt = BASE_DIR / rel   # <-- use BASE_DIR here too
#             if alt.exists():
#                 p = alt
#                 break
#         else:
#             raise FileNotFoundError(
#                 f"Could not find recipes CSV. Tried '{csv_path}' "
#                 f"and default locations under {BASE_DIR}"
#             )

#     df = pd.read_csv(p)

#     # ----- ingredients: convert big string -> list of tokens -----
#     def parse_ings(x):
#         if not isinstance(x, str):
#             return []

#         x = x.strip()

#         # if it looks like a Python list string -> try literal_eval first
#         if x.startswith("[") and x.endswith("]"):
#             try:
#                 val = literal_eval(x)
#                 if isinstance(val, list):
#                     return _normalize_list(val)
#             except Exception:
#                 pass

#         # fallback: treat as comma-separated string
#         parts = [p.strip() for p in x.split(",")]
#         return _normalize_list(parts)

#     if "ingredients" not in df.columns:
#         raise ValueError("CSV has no 'ingredients' column – check the file format.")

#     df["ingredients_norm"] = df["ingredients"].apply(parse_ings)

#     # ----- pick a display name -----
#     name_col = None
#     for col in ["recipe_name", "title", "name"]:
#         if col in df.columns:
#             name_col = col
#             break

#     if name_col is not None:
#         df["display_name"] = df[name_col].fillna("").astype(str)
#     else:
#         # final fallback: use row index as name
#         df["display_name"] = df.index.astype(str)

#     return df[["display_name", "ingredients_norm"]].copy()

# def match_recipes(user_ings: List[str], df: pd.DataFrame, top_k: int = 3) -> List[Tuple[str, int, int]]:
#     """
#     Simple OR-match scorer:

#       - user_ings: list like ["chicken", "onion", "garlic"]
#       - for each recipe, we count how many of these words appear as substrings
#         inside any of the ingredient phrases.

#       score = number of user ingredients that appear in the recipe
#       returns top_k items as (name, matches, total_recipe_ings)
#     """
#     if not user_ings:
#         return []

#     # normalize user inputs once
#     user_norm = _normalize_list(user_ings)

#     scores: List[Tuple[str, int, int]] = []

#     for _, row in df.iterrows():
#         recipe_ings = row["ingredients_norm"]  # list of normalized strings

#         # for each user ingredient, check if it's contained in ANY recipe ingredient string
#         matches = 0
#         for u in user_norm:
#             if any(u in ing for ing in recipe_ings):
#                 matches += 1

#         if matches > 0:
#             scores.append((row["display_name"], matches, len(recipe_ings)))

#     # sort: more matches first; tie-breaker = shorter recipe
#     scores.sort(key=lambda t: (-t[1], t[2]))
#     return scores[:top_k]


# scripts/recipe_search.py
from __future__ import annotations

from ast import literal_eval
from pathlib import Path
from typing import List, Dict

import pandas as pd

# Project root: PantryPal/
BASE_DIR = Path(__file__).resolve().parents[1]


def _normalize(s: str) -> str:
    """Lowercase + trim + collapse inner spaces."""
    return " ".join(s.lower().strip().split())


def _normalize_list(xs: List[str]) -> List[str]:
    """Apply _normalize to a list and drop empty items."""
    return [_normalize(x) for x in xs if isinstance(x, str) and x.strip()]


def load_recipes(csv_path: str | Path) -> pd.DataFrame:
    """
    Loads your Kaggle-style recipe CSV.

    We expect columns:
      - 'ingredients'  : long string ("3 tbsp butter, 2 apples, ...")
      - 'recipe_name'  : recipe title  (or 'title' / 'name' as fallback)
    """
    # 1) Resolve the main path relative to project root
    p = Path(csv_path)
    if not p.is_absolute():
        p = BASE_DIR / p

    # 2) Fallback locations if that exact path doesn't exist
    if not p.exists():
        for alt in [
            BASE_DIR / "data/raw/recipes.csv",
            BASE_DIR / "data/cleaned/recipes.csv",
            BASE_DIR / "recipes.csv",
        ]:
            if alt.exists():
                p = alt
                break

    df = pd.read_csv(p)

    # ----- ingredients: convert big string -> list of tokens -----
    def parse_ings(x):
        if not isinstance(x, str):
            return []

        x = x.strip()

        # Case 1: looks like "['salt', 'pepper']" → try literal_eval
        if x.startswith("[") and x.endswith("]"):
            try:
                val = literal_eval(x)
                if isinstance(val, list):
                    return _normalize_list(val)
            except Exception:
                pass

        # Case 2: treat as comma-separated string
        parts = [p.strip() for p in x.split(",")]
        return _normalize_list(parts)

    if "ingredients" not in df.columns:
        raise ValueError("CSV has no 'ingredients' column – check the file format.")

    df["ingredients_norm"] = df["ingredients"].apply(parse_ings)

    # ----- pick a display name -----
    name_col = None
    for col in ["recipe_name", "title", "name"]:
        if col in df.columns:
            name_col = col
            break

    if name_col is not None:
        df["display_name"] = df[name_col].fillna("").astype(str)
    else:
        # final fallback: use row index as name
        df["display_name"] = df.index.astype(str)

    return df[["display_name", "ingredients_norm"]].copy()


def match_recipes(
    user_ings: List[str],
    df: pd.DataFrame,
    quota: int = 7,
    hi_thresh: float = 0.7,   # ≥ 70% of *your* ingredients used
    lo_thresh: float = 0.4,   # ≥ 40% of your ingredients used (for filling quota)
) -> List[Dict]:
    """
    Quota-based matcher.

    For each recipe we compute:
      - matches     : how many user ingredients appear (substring match)
      - pct_recipe  : matches / recipe_size
      - pct_user    : matches / number_of_user_ingredients
      - score       : 0.5 * pct_recipe + 0.5 * pct_user

    Then:
      1) Take recipes with pct_user >= hi_thresh, sorted by score, up to 'quota'.
      2) If still short, fill with recipes pct_user >= lo_thresh.
    Returns list of dicts:
      'name', 'matches', 'pct_recipe', 'pct_user', 'score', 'recipe_size'
    """
    if not user_ings:
        return []

    user_norm_list = _normalize_list(user_ings)
    user_norm = set(user_norm_list)
    if not user_norm:
        return []

    candidates: List[Dict] = []

    for _, row in df.iterrows():
        recipe_ings = row["ingredients_norm"]
        if not recipe_ings:
            continue

        recipe_size = len(recipe_ings)

        # substring-based matching: "chicken" matches "1 lb chicken breast"
        matches = 0
        for u in user_norm:
            if any(u in ing for ing in recipe_ings):
                matches += 1

        if matches == 0:
            continue

        pct_recipe = matches / recipe_size
        pct_user = matches / len(user_norm)
        score = 0.5 * pct_recipe + 0.5 * pct_user

        candidates.append(
            {
                "name": row["display_name"],
                "matches": matches,
                "pct_recipe": pct_recipe,
                "pct_user": pct_user,
                "score": score,
                "recipe_size": recipe_size,
            }
        )

    if not candidates:
        return []

    # sort best → worst; ties broken by shorter recipes
    candidates.sort(key=lambda c: (-c["score"], c["recipe_size"]))

    selected: List[Dict] = []

    # Pass 1: strong matches based on pct_user
    for c in candidates:
        if c["pct_user"] >= hi_thresh:
            selected.append(c)
        if len(selected) >= quota:
            return selected

    # Pass 2: fill remaining quota with okay matches
    for c in candidates:
        if c in selected:
            continue
        if c["pct_user"] >= lo_thresh:
            selected.append(c)
        if len(selected) >= quota:
            break

    return selected

