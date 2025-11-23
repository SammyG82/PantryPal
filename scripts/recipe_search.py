# scripts/recipe_search.py
from __future__ import annotations
from ast import literal_eval
from pathlib import Path
from typing import List, Dict, Set
import re
import pandas as pd

# -------------------------------------------------
# PATHS
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]

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
    
    # quality descriptors - REMOVED preparation methods like dried, smoked, roasted
    "fresh", "freshly", "extra", "extra-virgin",
    "low-fat", "fat-free", "reduced", "light",
    
    # state/preparation - these should be ignored so "dried tomatoes" = "tomatoes"
    "dried", "smoked", "roasted", "grilled", "fried", "baked",
    "toasted", "cooked", "raw",
    
    # connectors
    "and", "or", "with", "without", "of", "in", "for", "to",
    "taste", "divided", "optional", "recipe", "can", "package",
}

def _normalize(s: str) -> str:
    """Lowercase + trim + collapse inner spaces."""
    return " ".join(s.lower().strip().split())

def _remove_numbers(text: str) -> str:
    """Remove integers and simple fractions like 1/2, 3/4."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"\d+\/\d+", " ", text)   # fractions
    text = re.sub(r"\d+", " ", text)        # whole numbers
    return text

def _clean_ingredient_to_core(ing: str) -> str:
    """
    Extract the CORE ingredient name only.
    
    Examples:
      '1/2 kg skinless chicken' -> 'chicken'
      'Dried Tomatoes' -> 'tomatoes'
      'fresh basil leaves' -> 'basil'
      '3 cloves garlic' -> 'garlic'
    
    Returns ONE core ingredient name, not multiple variants.
    """
    if not isinstance(ing, str):
        return ""
    
    ing = ing.lower()
    ing = _remove_numbers(ing)
    
    # Remove punctuation but keep spaces
    ing = re.sub(r"[^\w\s]", " ", ing)
    ing = re.sub(r"\s+", " ", ing).strip()
    
    # Split and filter
    tokens: List[str] = []
    for tok in ing.split():
        # Skip stopwords
        if tok in ING_STOPWORDS:
            continue
        # Keep meaningful words (3+ chars typically)
        if len(tok) > 2:
            tokens.append(tok)
    
    if not tokens:
        return ""
    
    # Strategy: Take the LAST meaningful word as the core ingredient
    # This works because ingredient phrases are usually:
    # [quantity] [preparation] [core_ingredient]
    # Examples:
    #   "skinless chicken breast" -> last word = "breast" but we want "chicken"
    #   "fresh basil" -> last word = "basil" ✓
    #   "dried tomatoes" -> last word = "tomatoes" ✓
    
    # Special handling for common multi-word ingredients
    phrase = " ".join(tokens)
    
    # Handle plurals: tomatoes -> tomato, potatoes -> potato
    last_word = tokens[-1]
    if last_word.endswith("oes"):  # tomatoes, potatoes
        singular = last_word[:-2]
        return singular
    elif last_word.endswith("es") and len(last_word) > 4:  # catches some plurals
        # Be careful: "cheese" shouldn't become "chees"
        if not last_word.endswith(("eese", "ose")):
            singular = last_word[:-2]
            return singular
    elif last_word.endswith("s") and len(last_word) > 3:
        # Remove trailing 's' for most plurals
        # But keep words like "bass", "grass" that naturally end in 's'
        if not last_word.endswith("ss"):
            singular = last_word[:-1]
            return singular
    
    return last_word

def _normalize_list(xs: List[str]) -> List[str]:
    """Apply _normalize + dedupe to a list and drop empty items."""
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
    """Return the first existing column name from candidates, or None."""
    for name in candidates:
        if name in df.columns:
            return name
    return None

def _extract_grams(text: str, label: str) -> float:
    """Extract '<number>g' after a label inside the nutrition string."""
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

# -------------------------------------------------
# LOAD & PREPARE DATAFRAME
# -------------------------------------------------
def load_recipes(csv_path: str | Path) -> pd.DataFrame:
    """
    Loads your recipe CSV and returns a normalized DataFrame.
    Each recipe gets a list of CORE ingredient names (one per ingredient).
    """
    p = Path(csv_path)
    if not p.is_absolute():
        p = BASE_DIR / p
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
    
    def parse_ings(x):
        """Parse ingredient list and extract core ingredient names."""
        if not isinstance(x, str):
            return []
        
        x = x.strip()
        core_ingredients: List[str] = []
        
        # Try parsing as Python list
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
        
        # Fallback: comma-separated
        parts = [p.strip() for p in x.split(",")]
        for p in parts:
            core = _clean_ingredient_to_core(p)
            if core:
                core_ingredients.append(core)
        
        return _normalize_list(core_ingredients)
    
    if "ingredients" not in df.columns:
        raise ValueError("CSV has no 'ingredients' column")
    
    df["ingredients_norm"] = df["ingredients"].apply(parse_ings)
    
    # Display name
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
    
    # Nutrition parsing
    if "nutrition" in df.columns:
        out["protein_g"] = df["nutrition"].apply(lambda s: _extract_grams(s, "Protein"))
        out["fat_g"] = df["nutrition"].apply(lambda s: _extract_grams(s, "Total Fat"))
        out["fiber_g"] = df["nutrition"].apply(lambda s: _extract_grams(s, "Dietary Fiber"))
        out["sugar_g"] = df["nutrition"].apply(lambda s: _extract_grams(s, "Total Sugars"))
        out["carbs_g"] = df["nutrition"].apply(lambda s: _extract_grams(s, "Total Carbohydrate"))
    else:
        for col in ["protein_g", "fat_g", "fiber_g", "sugar_g", "carbs_g"]:
            out[col] = 0.0
    
    return out

# -------------------------------------------------
# HEALTH SCORE LOGIC
# -------------------------------------------------
def _compute_health_score(row: pd.Series) -> float:
    """Health score in [0,1] based on macros."""
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

# -------------------------------------------------
# MATCHING LOGIC - FIXED
# -------------------------------------------------
def match_recipes(
    user_ings: List[str],
    df: pd.DataFrame,
    quota: int = 7,
    hi_thresh: float = 0.5,
    lo_thresh: float = 0.3,
) -> List[Dict]:
    """
    Match recipes based on core ingredients.
    
    Logic:
    1. User enters: ["Garlic", "Chicken", "Egg", "Tomato"]
       -> Cleaned to: ["garlic", "chicken", "egg", "tomato"]
    
    2. Recipe has: ["1/2 kg skinless chicken", "Dried Tomatoes", "Garlic", "Pepper", "Salt"]
       -> Cleaned to: ["chicken", "tomato", "garlic", "pepper", "salt"]
    
    3. Match calculation:
       - matches = 3 (chicken, tomato, garlic are in both)
       - pct_recipe = 3/5 = 60% (3 out of 5 recipe ingredients matched)
       - pct_user = 3/4 = 75% (3 out of 4 user ingredients used)
    """
    if not user_ings:
        return []
    
    # Clean user ingredients to core names
    user_cores: Set[str] = set()
    for u in user_ings:
        core = _clean_ingredient_to_core(u)
        if core:
            user_cores.add(core)
    
    if not user_cores:
        return []
    
    candidates: List[Dict] = []
    
    # Score all recipes
    for _, row in df.iterrows():
        recipe_cores = row["ingredients_norm"]
        if not recipe_cores:
            continue
        
        recipe_set = set(recipe_cores)
        recipe_size = len(recipe_set)
        
        # Find intersection
        matched_ingredients = user_cores & recipe_set
        matches = len(matched_ingredients)
        
        if matches == 0:
            continue
        
        # Calculate percentages
        pct_recipe = matches / recipe_size if recipe_size > 0 else 0
        pct_user = matches / len(user_cores) if user_cores else 0
        
        # Weighted score: favor recipes that use more of user's ingredients
        match_score = 0.6 * pct_user + 0.4 * pct_recipe
        
        health_score = _compute_health_score(row)
        
        candidates.append({
            "name": row["display_name"],
            "matches": matches,
            "pct_recipe": pct_recipe,
            "pct_user": pct_user,
            "score": match_score,
            "recipe_size": recipe_size,
            "health_score": health_score,
            "protein_g": float(row.get("protein_g", 0.0) or 0.0),
            "fat_g": float(row.get("fat_g", 0.0) or 0.0),
            "sugar_g": float(row.get("sugar_g", 0.0) or 0.0),
            "carbs_g": float(row.get("carbs_g", 0.0) or 0.0),
        })
    
    if not candidates:
        return []
    
    # Sort by match score, then by smaller recipe size (simpler recipes first)
    candidates.sort(key=lambda c: (-c["score"], c["recipe_size"]))
    
    selected: List[Dict] = []
    
    # Pass 1: Strong matches (>= 50% of user ingredients used)
    for c in candidates:
        if c["pct_user"] >= hi_thresh:
            selected.append(c)
        if len(selected) >= quota:
            return selected
    
    # Pass 2: Okay matches (>= 30% of user ingredients used)
    for c in candidates:
        if c in selected:
            continue
        if c["pct_user"] >= lo_thresh:
            selected.append(c)
        if len(selected) >= quota:
            return selected
    
    # Pass 3: Fill remaining slots with best available
    for c in candidates:
        if c in selected:
            continue
        selected.append(c)
        if len(selected) >= quota:
            break
    
    return selected