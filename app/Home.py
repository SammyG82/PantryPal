import streamlit as st

# ------------------ PAGE CONFIG (MUST BE FIRST) ------------------
st.set_page_config(page_title="PantryPal", page_icon="🥕", layout="wide")

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
    <div style="width:100%; text-align:center; margin-top:10px; margin-bottom:20px;">
        <h1>🥕 PantryPal</h1>
        <div class="callout">
            <p class="lead"><b>Welcome to PantryPal!</b> Not sure what to cook? <b>We've got you covered.</b></p>
            <p class="lead"><b>You can either:</b></p>
            <ul>
                <b>Upload photos</b> of the ingredients you have<br>
                <b>Type</b> your ingredients in the box
            </ul>
            <p class="lead">Hit <b>Cook</b> when you're done and we'll show recipes from <b> 💪 Healthiest → Cheat Day</b> 🤩</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------ MAIN CONTENT ------------------
content_container = st.container()

with content_container:
    left, right = st.columns(2, gap="large")

    # ---- LEFT COLUMN: IMAGE UPLOADER ----
    with left:
        render_image_uploader()

    # ---- RIGHT COLUMN: INGREDIENT INPUT ----
    with right:
        render_ingredient_input()

    # ---- COOK BUTTON ----
    render_cook_button()
