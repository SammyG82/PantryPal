import streamlit as st

st.set_page_config(page_title="Results", page_icon="🍽️", layout="wide")

st.title("🍽️ Your Recipes")

# Check if user has cooked
if "cooked" not in st.session_state or not st.session_state.cooked:
    st.error("Please go back and add ingredients first.")
    st.stop()

# ---------------- Ingredients ----------------
st.write("### Ingredients you provided:")

if st.session_state.ingredients:
    # Flex container for badges
    st.markdown('<div style="display:flex; flex-wrap: wrap;">', unsafe_allow_html=True)
    for ing in st.session_state.ingredients:
        st.markdown(
            f'<div style="display:inline-block; padding:0.4rem 0.8rem; margin:0.25rem; \
            border-radius:12px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); \
            font-weight:600;">{ing}</div>', unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No ingredients provided.")

# ---------------- Images ----------------
st.write("### Images uploaded:")
if st.session_state.images:
    for img in st.session_state.images:
        st.image(img["bytes"], caption=img["name"], use_container_width=True)
else:
    st.info("No images uploaded.")

# ---------------- Placeholder ----------------
st.info("AI recipe generation coming soon!")
