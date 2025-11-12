import streamlit as st

st.set_page_config(page_title="Results • PantryPal", page_icon="🥗", layout="wide")

# ------------------ STYLES ------------------
st.markdown("""
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
</style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.markdown('<div class="header-wrap"><h1>🥗 Your Recipe Matches</h1></div>', unsafe_allow_html=True)

# ------------------ GET DATA ------------------
imgs = st.session_state.get("images", [])
ings = st.session_state.get("ingredients", [])
cooked = st.session_state.get("cooked", False)

# Check if user actually clicked Cook button
if not cooked:
    st.warning("⚠️ You haven't cooked yet! Go back to **Home** and click the **Cook** button.")
    if st.button("⬅️ Back to Home", use_container_width=True):
        st.switch_page("Home.py")
    st.stop()

if not imgs and not ings:
    st.warning("⚠️ No inputs found. Go back to **Home** and add images or ingredients.")
    if st.button("⬅️ Back to Home", use_container_width=True):
        st.switch_page("Home.py")
    st.stop()

# ------------------ SHOW INPUTS ------------------
with st.expander("📦 Your ingredients", expanded=True):
    left, right = st.columns(2)
    
    with left:
        if ings:
            st.write("**Text ingredients:**")
            for x in ings:
                st.write(f"- {x}")
        else:
            st.write("*No text ingredients provided.*")
    
    with right:
        if imgs:
            st.write(f"**Photos: ({len(imgs)} uploaded)**")
            # Show thumbnails in a grid
            cols = st.columns(3)
            for idx, img in enumerate(imgs[:3]):  # Show first 3
                with cols[idx % 3]:
                    st.image(img["bytes"], caption=img["name"], use_container_width=True)
            if len(imgs) > 3:
                st.caption(f"+ {len(imgs) - 3} more photos")
        else:
            st.write("*No photos provided.*")

st.divider()

# ------------------ MOCK RECIPES ------------------
st.subheader("Recipes ranked by health score")

# Mock recipe data (you'll replace this with real matching later)
mock_recipes = [
    {
        "name": "Grilled Veggie Power Bowl",
        "health": "Super Healthy",
        "badge_class": "badge-healthy",
        "description": "Packed with vitamins, fiber, and protein. Low calories, high nutrition.",
        "ingredients_match": "8/10 ingredients matched"
    },
    {
        "name": "Chicken & Vegetable Stir-Fry",
        "health": "Balanced",
        "badge_class": "badge-balanced",
        "description": "Good protein-to-carb ratio. Moderate calories with healthy fats.",
        "ingredients_match": "7/10 ingredients matched"
    },
    {
        "name": "Creamy Pasta Carbonara",
        "health": "Balanced",
        "badge_class": "badge-balanced",
        "description": "Higher in calories but includes vegetables. Good for active days.",
        "ingredients_match": "6/10 ingredients matched"
    },
    {
        "name": "Loaded Nachos Supreme",
        "health": "Cheat Day",
        "badge_class": "badge-cheat",
        "description": "High calories, high satisfaction! Perfect for treating yourself.",
        "ingredients_match": "5/10 ingredients matched"
    },
]

for i, recipe in enumerate(mock_recipes, start=1):
    st.markdown(f"""
    <div class="recipe-card">
        <h3>
            {i}. {recipe['name']}
            <span class="health-badge {recipe['badge_class']}">{recipe['health']}</span>
        </h3>
        <p>{recipe['description']}</p>
        <p><b>Match:</b> {recipe['ingredients_match']}</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ------------------ ACTIONS ------------------
col1, col2 = st.columns(2)
with col1:
    if st.button("⬅️ Back to Home", use_container_width=True):
        # Don't reset cooked flag - just go back
        st.switch_page("Home.py")
        
with col2:
    if st.button("🔄 Clear All & Start Over", use_container_width=True, type="primary"):
        st.session_state.ingredients = []
        st.session_state.images = []
        st.session_state.uploader_key += 1
        st.session_state.cooked = False  # Only reset cooked flag when clearing
        st.success("✅ Cleared! Redirecting...")
        st.switch_page("Home.py")