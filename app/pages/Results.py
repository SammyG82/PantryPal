# app/pages/Results.py
import os
import sys
from pathlib import Path

import streamlit as st

# -------------------------------------------------
# MAKE PROJECT ROOT IMPORTABLE FOR "scripts" MODULE
# -------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from scripts.recipe_search import load_recipes, match_recipes  # noqa: E402


# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Results • PantryPal", page_icon="🥗", layout="wide")

# -------------------------------------------------
# GLOBAL STYLES
# -------------------------------------------------
st.markdown(
    """
<style>
.header-wrap {text-align:center; margin-top:0.5rem; margin-bottom:1.25rem;}
.header-wrap h1 {font-size: 2.2rem; line-height: 1.1; margin: 0;}
.recipe-card {
  margin: 0.75rem 0; padding: 1rem 1.25rem;
  border: 1px solid rgba(255,255,255,0.08); border-radius: 14px;
  background: rgba(255,255,255,0.03);
}
.recipe-card h3 {margin: 0 0 0.5rem 0; font-size: 1.3rem;}
.recipe-card p {margin: 0.25rem 0; color: rgba(255,255,255,0.7);}
.health-badge {
  display: inline-block; padding: 0.25rem 0.75rem; border-radius: 8px;
  font-size: 0.85rem; font-weight: 600; margin-left: 0.5rem;
}
.badge-healthy {background: rgba(76, 175, 80, 0.2); color: #4CAF50;}
.badge-balanced {background: rgba(255, 193, 7, 0.2); color: #FFC107;}
.badge-cheat {background: rgba(244, 67, 54, 0.2); color: #F44336;}
.muted {color: rgba(255,255,255,0.5);}
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------
# HEADER
# -------------------------------------------------
st.markdown(
    '<div class="header-wrap"><h1>🥗 Your Recipe Matches</h1></div>',
    unsafe_allow_html=True,
)

# -------------------------------------------------
# GET SESSION STATE DATA
# -------------------------------------------------
imgs = st.session_state.get("images", [])
ings = st.session_state.get("ingredients", [])
cooked = st.session_state.get("cooked", False)

if not cooked:
    st.warning("⚠️ You haven't cooked yet! Go back to **Home** and click the **Cook** button.")
    if st.button("⬅️ Back to Home", use_container_width=True):
        st.switch_page("Home.py")
    st.stop()

if not imgs and not ings:
    st.warning("⚠️ No inputs found. Add ingredients on the Home page.")
    if st.button("⬅️ Back to Home", use_container_width=True):
        st.switch_page("Home.py")
    st.stop()

# -------------------------------------------------
# SHOW USER INPUTS
# -------------------------------------------------
with st.expander("📦 Your ingredients", expanded=True):
    left, right = st.columns(2)

    with left:
        st.write("**Text ingredients:**" if ings else "*No text ingredients provided.*")
        for x in ings:
            st.write(f"- {x}")

    with right:
        if imgs:
            st.write(f"**Photos: ({len(imgs)} uploaded)**")
            cols = st.columns(3)
            for idx, img in enumerate(imgs[:3]):
                with cols[idx % 3]:
                    st.image(img["bytes"], caption=img["name"], use_container_width=True)
            if len(imgs) > 3:
                st.caption(f"+ {len(imgs) - 3} more photos")
        else:
            st.write("*No photos provided.*")

st.divider()

# -------------------------------------------------
# LOAD DATASET
# -------------------------------------------------
@st.cache_data(show_spinner=False)
def _load_df():
    # recipes live at data/raw/recipes.csv relative to project root
    return load_recipes("data/raw/recipes.csv")


df = _load_df()

st.subheader("Recipes based on your ingredients & health")


# -------------------------------------------------
# BADGE HELPERS
# -------------------------------------------------
def _badge_for_match(pct_user: float):
    """Badge for ingredient-match quality (how much of *your* list is used)."""
    pct = pct_user * 100
    if pct >= 80:
        return "Great Match", "badge-healthy"
    elif pct >= 60:
        return "Good Match", "badge-balanced"
    else:
        return "Loose Match", "badge-cheat"


def _badge_for_health(score: float):
    """Badge for healthiness (0–1)."""
    if score >= 0.70:
        return "Super Healthy", "badge-healthy"
    elif score >= 0.40:
        return "Balanced", "badge-balanced"
    else:
        return "Cheat Day-ish", "badge-cheat"


# -------------------------------------------------
# MATCH RECIPES
# -------------------------------------------------
if ings:
    results = match_recipes(ings, df, quota=7)

    if not results:
        st.info("No direct matches found. Try adding more common ingredients ✨")
    else:
        # left column: best by ingredient overlap (already sorted by match score)
        # right column: same recipes, but sorted by health_score
        col_match, col_health = st.columns(2)

        with col_match:
            st.markdown("#### 🔍 Best ingredient matches")
            for i, rec in enumerate(results, start=1):
                name = rec["name"]
                hits = rec["matches"]
                total = rec["recipe_size"]
                pct_u = int(rec["pct_user"] * 100)

                label, badge_class = _badge_for_match(rec["pct_user"])

                st.markdown(
                    f"""
                    <div class="recipe-card">
                        <h3>{i}. {name}
                            <span class="health-badge {badge_class}">{label}</span>
                        </h3>
                        <p><b>Matched ingredients:</b> {hits} / {total}</p>
                        <p><b>Of your list used:</b> {pct_u}%</p>
                        <p class="muted">Ranked by how well the recipe fits what you have.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col_health:
            st.markdown("#### 💚 Healthiest among these")
            by_health = sorted(results, key=lambda r: r["health_score"], reverse=True)

            for i, rec in enumerate(by_health, start=1):
                name = rec["name"]
                hscore = rec["health_score"]
                protein = rec["protein_g"]
                fat = rec["fat_g"]
                sugar = rec["sugar_g"]
                carbs = rec["carbs_g"]

                label, badge_class = _badge_for_health(hscore)
                pct_h = int(hscore * 100)

                st.markdown(
                    f"""
                    <div class="recipe-card">
                        <h3>{i}. {name}
                            <span class="health-badge {badge_class}">{label}</span>
                        </h3>
                        <p><b>Health score:</b> {pct_h}/100</p>
                        <p><b>Approx. macros (per serving, from dataset):</b></p>
                        <p>Protein: {protein:.1f} g • Fat: {fat:.1f} g
                        • Sugar: {sugar:.1f} g • Carbs: {carbs:.1f} g</p>
                        <p class="muted">Score based on protein, fat, sugar and net carbs.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )       

else:
    st.info("Type some ingredients on the Home page first.")

st.divider()

# -------------------------------------------------
# ACTION BUTTONS
# -------------------------------------------------
left_btn, right_btn = st.columns(2)

with left_btn:
    if st.button("⬅️ Back to Home", use_container_width=True):
        st.switch_page("Home.py")

with right_btn:
    if st.button("🔄 Clear & Start Over", use_container_width=True, type="primary"):
        st.session_state.ingredients = []
        st.session_state.images = []
        st.session_state.cooked = False
        st.session_state.uploader_key += 1
        st.success("Reset!")
        st.switch_page("Home.py")
