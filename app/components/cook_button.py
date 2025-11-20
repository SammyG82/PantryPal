import streamlit as st

def render_cook_button():
    st.divider()
    if st.button("🍳 Cook!", use_container_width=True):
        if not st.session_state.images and not st.session_state.ingredients:
            st.error("⚠️ Please add at least one ingredient or photo before cooking!")
        else:
            st.session_state.cooked = True
            st.switch_page("pages/Results.py")
