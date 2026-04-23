"""
Convert RAW_recipes.csv from the Food.com Kaggle dataset into
the format PantryPal's backend expects, saved to data/raw/recipes.csv.

Usage:
    python scripts/prepare_foodcom.py ~/Downloads/archive/RAW_recipes.csv
"""

import ast
import sys
from pathlib import Path

import pandas as pd

INPUT  = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads/archive/RAW_recipes.csv"
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "recipes.csv"

# PDV daily values (grams) used to convert % daily value → grams
FAT_DV    = 78.0
SUGAR_DV  = 50.0
PROTEIN_DV = 50.0
CARBS_DV  = 275.0


def parse_nutrition(raw) -> str:
    """Convert Food.com nutrition list to text format the backend expects."""
    try:
        vals = ast.literal_eval(raw) if isinstance(raw, str) else raw
        calories   = round(float(vals[0]))
        fat_g      = round(float(vals[1]) / 100 * FAT_DV, 1)
        sugar_g    = round(float(vals[2]) / 100 * SUGAR_DV, 1)
        protein_g  = round(float(vals[4]) / 100 * PROTEIN_DV, 1)
        carbs_g    = round(float(vals[6]) / 100 * CARBS_DV, 1)
        return (
            f"Calories {calories} Total Fat {fat_g}g "
            f"Protein {protein_g}g Total Sugars {sugar_g}g "
            f"Total Carbohydrate {carbs_g}g Dietary Fiber 0g"
        )
    except Exception:
        return ""


def minutes_to_str(mins) -> str:
    try:
        m = int(float(mins))
        if m <= 0:
            return ""
        if m < 60:
            return f"{m} mins"
        h, rem = divmod(m, 60)
        return f"{h} hr {rem} mins" if rem else f"{h} hr"
    except Exception:
        return ""


def build_url(row) -> str:
    slug = str(row["name"]).strip().lower().replace(" ", "-")
    return f"https://www.food.com/recipe/{slug}-{int(row['id'])}"


print(f"Reading {INPUT} ...")
df = pd.read_csv(INPUT)
print(f"  {len(df):,} rows loaded")

out = pd.DataFrame()
out["recipe_name"] = df["name"].str.strip().str.title()
out["ingredients"] = df["ingredients"]
out["nutrition"]   = df["nutrition"].apply(parse_nutrition)
out["cook_time"]   = df["minutes"].apply(minutes_to_str)
out["url"]         = df.apply(build_url, axis=1)

# Drop rows with no ingredients
out = out[out["ingredients"].notna() & (out["ingredients"].str.strip() != "")]

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUTPUT, index=False)
print(f"  Saved {len(out):,} recipes → {OUTPUT}")
