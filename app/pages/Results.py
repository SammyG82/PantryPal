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
/* Gradient background */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header-wrap {
    text-align: center; 
    margin-top: 1rem; 
    margin-bottom: 2rem;
}
.header-wrap h1 {
    font-size: 3rem; 
    line-height: 1.1; 
    margin: 0;
    font-weight: 800;
    background: linear-gradient(135deg, #fff 0%, #f0f0f0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.recipe-card {
    margin: 1rem 0; 
    padding: 1.5rem 1.75rem;
    border: 2px solid rgba(255,255,255,0.2); 
    border-radius: 20px;
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.recipe-card:hover {
    transform: translateX(8px) translateY(-2px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.2);
    background: rgba(255,255,255,0.2);
    border-color: rgba(255,255,255,0.3);
}
.recipe-card h3 {
    margin: 0 0 1rem 0; 
    font-size: 1.6rem;
    font-weight: 700;
    color: #fff;
}
.recipe-card p {
    margin: 0.5rem 0; 
    color: rgba(255,255,255,0.95);
    font-size: 1.1rem;
    line-height: 1.6;
}
.health-badge {
    display: inline-block; 
    padding: 0.4rem 1.2rem; 
    border-radius: 25px;
    font-size: 0.85rem; 
    font-weight: 700; 
    margin-left: 1rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}
.badge-healthy {
    background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%); 
    color: #fff;
}
.badge-balanced {
    background: linear-gradient(135deg, #f2994a 0%, #f2c94c 100%); 
    color: #fff;
}
.badge-cheat {
    background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); 
    color: #fff;
}
.muted {
    color: rgba(255,255,255,0.65);
    font-size: 0.95rem;
    font-style: italic;
    margin-top: 0.75rem;
}
.column-header {
    background: rgba(255,255,255,0.1);
    padding: 1rem 1.5rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255,255,255,0.2);
}
.column-header h4 {
    margin: 0;
    color: #fff;
    font-size: 1.4rem;
    font-weight: 700;
}

/* Button styles */
.stButton > button {
    padding: 0.75rem 2rem;
    border-radius: 16px;
    font-weight: 600;
    font-size: 1.1rem;
    transition: all 0.3s ease;
    border: 2px solid rgba(255,255,255,0.3);
}

/* Enhanced expander */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.15) !important;
    font-weight: 600;
    font-size: 1.2rem;
    color: #fff;
}

/* Text color fixes */
p, span, div, li {
    color: #fff;
}
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------
# HEADER
# -------------------------------------------------
st.markdown(
    '<div class="header-wrap"><h1>🥗 Your Recipe Matches</h1><p style="font-size: 1.2rem; color: rgba(255,255,255,0.9); margin-top: 1rem;">Personalized recipes based on your ingredients</p></div>',
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
    st.markdown("""
        <div style="background: rgba(255,255,255,0.05); 
                    padding: 1.5rem; 
                    border-radius: 16px;">
        </div>
    """, unsafe_allow_html=True)
    
    left, right = st.columns(2)

    with left:
        if ings:
            st.markdown("### 📝 Text ingredients:")
            for x in ings:
                st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.08); 
                                padding: 0.5rem 1rem; 
                                border-radius: 10px; 
                                margin-bottom: 0.5rem;
                                display: inline-block;">
                        🥘 {x}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.write("*No text ingredients provided.*")

    with right:
        if imgs:
            st.markdown(f"### 📸 Photos: ({len(imgs)} uploaded)")
            cols = st.columns(3)
            for idx, img in enumerate(imgs[:3]):
                with cols[idx % 3]:
                    st.image(img["bytes"], caption=img["name"], use_container_width=True)
            if len(imgs) > 3:
                st.caption(f"+ {len(imgs) - 3} more photos")
        else:
            st.write("*No photos provided.*")

st.markdown("<br>", unsafe_allow_html=True)
st.divider()
st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------
# LOAD DATASET
# -------------------------------------------------
@st.cache_data(show_spinner=False)
def _load_df():
    # recipes live at data/raw/recipes.csv relative to project root
    return load_recipes("data/raw/recipes.csv")


with st.spinner("🔍 Searching through thousands of recipes..."):
    df = _load_df()

st.markdown("""
    <h2 style="text-align: center; color: #fff; margin: 2rem 0;">
        🎯 Perfect Recipes Just For You
    </h2>
""", unsafe_allow_html=True)


# -------------------------------------------------
# BADGE HELPERS
# -------------------------------------------------
def _badge_for_match(pct_user: float):
    """Badge for ingredient-match quality (how much of *your* list is used)."""
    pct = pct_user * 100
    if pct >= 70:
        return "💚 Strong Match", "badge-healthy"
    elif pct >= 40:
        return "✨ Good Match", "badge-balanced"
    else:
        return "🔍 Partial Match", "badge-cheat"


def _badge_for_health(score: float):
    """Badge for healthiness (0–1)."""
    if score >= 0.70:
        return "💪 Super Healthy", "badge-healthy"
    elif score >= 0.40:
        return "⚖️ Balanced", "badge-balanced"
    else:
        return "🍰 Cheat Day", "badge-cheat"


# -------------------------------------------------
# MATCH RECIPES
# -------------------------------------------------
if ings:
    results = match_recipes(ings, df, quota=7)

    if not results:
        st.info("No direct matches found. Try adding more common ingredients ✨")
    else:
        # Create two columns with headers
        col_match, col_health = st.columns(2)

        with col_match:
            st.markdown("""
                <div class="column-header">
                    <h4>🔍 Best Ingredient Matches</h4>
                </div>
            """, unsafe_allow_html=True)
            
            for i, rec in enumerate(results, start=1):
                name = rec["name"]
                hits = rec["matches"]
                total = rec["recipe_size"]
                pct_u = int(rec["pct_user"] * 100)

                label, badge_class = _badge_for_match(rec["pct_user"])

                st.markdown(
                    f"""
                    <div class="recipe-card">
                        <h3>#{i} {name}
                            <span class="health-badge {badge_class}">{label}</span>
                        </h3>
                        <p><b>✅ Matched ingredients:</b> {hits} of {total}</p>
                        <p><b>📊 Your ingredients used:</b> {pct_u}%</p>
                        <p class="muted">Ranked by ingredient compatibility</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col_health:
            st.markdown("""
                <div class="column-header">
                    <h4>💚 Healthiest Options</h4>
                </div>
            """, unsafe_allow_html=True)
            
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
                        <h3>#{i} {name}
                            <span class="health-badge {badge_class}">{label}</span>
                        </h3>
                        <p><b>💚 Health score:</b> {pct_h}/100</p>
                        <p><b>🥗 Nutrition per serving:</b></p>
                        <p style="margin-left: 1rem;">
                            🥩 Protein: {protein:.1f}g • 
                            🧈 Fat: {fat:.1f}g<br>
                            🍬 Sugar: {sugar:.1f}g • 
                            🍞 Carbs: {carbs:.1f}g
                        </p>
                        <p class="muted">Optimized for nutritional value</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )       

else:
    st.info("Type some ingredients on the Home page first.")

st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------
# ACTION BUTTONS
# -------------------------------------------------
col1, col2, col3 = st.columns([2, 1, 2])

with col1:
    if st.button("⬅️ Back to Home", use_container_width=True, type="secondary"):
        st.switch_page("Home.py")

with col3:
    if st.button("🔄 Start Fresh", use_container_width=True, type="primary"):
        st.session_state.ingredients = []
        st.session_state.images = []
        st.session_state.cooked = False
        st.session_state.uploader_key += 1
        st.success("✨ Reset! Starting fresh...")
        import time
        time.sleep(1)
        st.switch_page("Home.py")