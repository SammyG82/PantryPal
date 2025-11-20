import streamlit as st
import os
import sys
from pathlib import Path

# -------------------------------------------------
# MAKE PROJECT ROOT IMPORTABLE FOR "scripts" MODULE
# -------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from scripts.recipe_search import load_recipes, match_recipes  # uses your updated file

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
    st.warning(
        "⚠️ You haven't cooked yet! Go back to **Home** and click the **Cook** button."
    )
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
        st.write(
            "**Text ingredients:**" if ings else "*No text ingredients provided.*"
        )
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
    # path is relative to project root (PantryPal/)
    return load_recipes("data/raw/recipes.csv")


df = _load_df()

st.subheader("Recipes ranked by ingredient matches")

# -------------------------------------------------
# BADGE HELPER
# -------------------------------------------------
def _badge_for_pct(p: float):
    """Map pct_recipe → label + CSS class."""
    p = p * 100
    if p >= 80:
        return "Super Close Match", "badge-healthy"
    elif p >= 60:
        return "Good Match", "badge-balanced"
    else:
        return "Loose Match", "badge-cheat"


# -------------------------------------------------
# MATCH RECIPES
# -------------------------------------------------
if ings:
    # quota=7 → pick up to 7 recipes using our score + thresholds
    results = match_recipes(ings, df, quota=7)

    if not results:
        st.info("No direct matches found. Try adding more common ingredients ✨")
    else:
        for i, rec in enumerate(results, start=1):
            name = rec["name"]
            hits = rec["matches"]
            total = rec["recipe_size"]
            pct_r = int(rec["pct_recipe"] * 100)
            pct_u = int(rec["pct_user"] * 100)

            label, badge_class = _badge_for_pct(rec["pct_recipe"])

            st.markdown(
                f"""
            <div class="recipe-card">
                <h3>{i}. {name}
                    <span class="health-badge {badge_class}">{label}</span>
                </h3>
                <p><b>Matched ingredients:</b> {hits} / {total}
                   (<b>{pct_r}%</b> of this recipe)</p>
                <p><b>Of your list used:</b> {pct_u}%</p>
                <p class="muted">Top 7 recipes chosen using overlap scoring.</p>
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
left, right = st.columns(2)

with left:
    if st.button("⬅️ Back to Home", use_container_width=True):
        st.switch_page("Home.py")

with right:
    if st.button(
        "🔄 Clear & Start Over", use_container_width=True, type="primary"
    ):
        st.session_state.ingredients = []
        st.session_state.images = []
        st.session_state.cooked = False
        st.session_state.uploader_key += 1
        st.success("Reset!")
        st.switch_page("Home.py")
