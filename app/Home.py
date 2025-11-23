import streamlit as st

# ------------------ PAGE CONFIG (MUST BE FIRST) ------------------
st.set_page_config(page_title="PantryPal", page_icon="", layout="wide")

# ------------------ IMPORT STYLES & COMPONENTS ------------------
import styles
from components.image_upload import render_image_uploader
from components.ingredient_input import render_ingredient_input
from components.cook_button import render_cook_button

# Apply CSS after page config
styles.apply_styles()

# ------------------ SESSION STATE ------------------
defaults = {
    "ingredients": [],
    "images": [],
    "uploader_key": 0,
    "entry_key": 0,
    "cooked": False,
    "ingredient_warning": None,
}

for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ------------------ HEADER ------------------
st.markdown(
    """
    <div style="width:100%; text-align:center; margin-top:10px; margin-bottom:30px;">
        <h1 style="font-size: 4rem; margin-bottom: 0.5rem;">PantryPal</h1>
        <p style="font-size: 1.3rem; color: rgba(255,255,255,0.9); font-weight: 500; margin-bottom: 2rem;">
            Transform your ingredients into delicious recipes
        </p>
        <div class="callout">
            <p class="lead"><b>Welcome to PantryPal!</b> Not sure what to cook? <b>We've got you covered.</b></p>
            <p class="lead" style="font-size: 1.3rem; margin: 1.5rem 0;"><b>How it works:</b></p>
            <div style="display: flex; justify-content: center; gap: 3rem; margin: 2rem 0;">
                <div style="text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">📸</div>
                    <div style="font-size: 1.1rem;"><b>Upload Photos</b><br>of your ingredients</div>
                </div>
                <div style="text-align: center; font-size: 2rem; line-height: 3rem;">OR</div>
                <div style="text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">⌨️</div>
                    <div style="font-size: 1.1rem;"><b>Type Names</b><br>of what you have</div>
                </div>
            </div>
            <p class="lead" style="font-size: 1.2rem; margin-top: 2rem;">
                Then hit the <b style="font-size: 1.3rem;">COOK</b> button to see recipes from 
                <b style="color: #56ab2f;">💪 Healthiest</b> to <b style="color: #f45c43;">🤩 Cheat Day</b>
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------ MAIN CONTENT ------------------
# Add some spacing
st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

content_container = st.container()

with content_container:
    # Create columns with better spacing
    left, middle, right = st.columns([5, 1, 5])

    # ---- LEFT COLUMN: IMAGE UPLOADER ----
    with left:
        with st.container():
            st.markdown("""
                <div style="background: rgba(255,255,255,0.05); 
                            padding: 1.5rem; 
                            border-radius: 20px;
                            border: 1px solid rgba(255,255,255,0.1);">
                </div>
            """, unsafe_allow_html=True)
            render_image_uploader()

    # ---- MIDDLE COLUMN: Divider ----
    with middle:
        st.markdown("""
            <div style="display: flex; 
                        align-items: center; 
                        justify-content: center; 
                        height: 100%; 
                        padding-top: 100px;">
                <div style="font-size: 2rem; 
                            color: rgba(255,255,255,0.5); 
                            font-weight: 300;">
                    OR
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ---- RIGHT COLUMN: INGREDIENT INPUT ----
    with right:
        with st.container():
            st.markdown("""
                <div style="background: rgba(255,255,255,0.05); 
                            padding: 1.5rem; 
                            border-radius: 20px;
                            border: 1px solid rgba(255,255,255,0.1);">
                </div>
            """, unsafe_allow_html=True)
            render_ingredient_input()

    # ---- COOK BUTTON ----
    render_cook_button()