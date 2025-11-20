import streamlit as st
from utils.helpers import add_from_textbox, _current_input_key, _get_current_text

def render_ingredient_input():
    st.markdown('<div class="section-title">✍️ <h3>Type your ingredients</h3></div>', unsafe_allow_html=True)

    st.text_input(
        "Enter individual ingredient:",
        placeholder="e.g., Onion",
        key=_current_input_key(),
        on_change=add_from_textbox,
    )

    if st.session_state.get("ingredient_warning"):
        st.warning(st.session_state.ingredient_warning)

    if st.button("Add"):
        txt = _get_current_text().strip()
        if not txt:
            st.warning("Please input an ingredient")
        else:
            add_from_textbox()
            st.rerun()

    if st.session_state.ingredients:
        st.write("**Ingredients added:**")
        for i, ing in enumerate(st.session_state.ingredients):
            c1, c2 = st.columns([6, 1])
            with c1:
                st.write(f"- {ing}")
            with c2:
                if st.button("❌", key=f"del_ing_{i}"):
                    st.session_state.ingredients.pop(i)
                    st.rerun()

        if st.button("Clear All Ingredients"):
            st.session_state.ingredients.clear()
            st.rerun()
    else:
        st.info("No ingredients added yet.")