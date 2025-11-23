import streamlit as st
from utils.helpers import add_from_textbox, _current_input_key, _get_current_text

def render_ingredient_input():
    st.markdown("""
        <div class="section-title">
            <span style="font-size: 1.8rem;">✍️</span>
            <h3>Type your ingredients</h3>
        </div>
    """, unsafe_allow_html=True)

    # Create a more visually appealing input area
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.text_input(
            "Enter individual ingredient:",
            placeholder="e.g., Onion, Tomatoes, Chicken...",
            key=_current_input_key(),
            on_change=add_from_textbox,
            label_visibility="collapsed"
        )
    
    with col2:
        if st.button("➕ Add", use_container_width=True, type="primary"):
            txt = _get_current_text().strip()
            if not txt:
                st.session_state.ingredient_warning = "Please input an ingredient"
            else:
                add_from_textbox()
                st.session_state.ingredient_warning = None
                st.rerun()

    # Display warning message below the input if needed
    if st.session_state.get("ingredient_warning"):
        st.markdown("""
            <div style="background: rgba(255,200,0,0.2); 
                        padding: 0.75rem 1rem; 
                        border-radius: 12px; 
                        border: 1px solid rgba(255,200,0,0.4);
                        margin-top: 0.5rem;
                        margin-bottom: 0.5rem;">
                <span style="color: #fff; font-weight: 500;">
                    ⚠️ {}
                </span>
            </div>
        """.format(st.session_state.ingredient_warning), unsafe_allow_html=True)
        # Clear the warning after displaying it
        st.session_state.ingredient_warning = None

    if st.session_state.ingredients:
        # Create a nice container for the ingredients list
        st.markdown("""
            <div style="background: rgba(255,255,255,0.1); 
                        padding: 1.25rem; 
                        border-radius: 16px; 
                        border: 1px solid rgba(255,255,255,0.2);
                        margin-top: 1.5rem;">
                <h4 style="color: #fff; margin-top: 0; margin-bottom: 1rem; font-size: 1.2rem;">
                    📝 Your Ingredients ({})
                </h4>
            </div>
        """.format(len(st.session_state.ingredients)), unsafe_allow_html=True)
        
        # Display ingredients in a grid layout with delete buttons
        for i, ing in enumerate(st.session_state.ingredients):
            c1, c2 = st.columns([8, 1])
            with c1:
                st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.08); 
                                padding: 0.5rem 1rem; 
                                border-radius: 10px; 
                                margin-bottom: 0.5rem;
                                border: 1px solid rgba(255,255,255,0.15);
                                display: flex;
                                align-items: center;">
                        <span style="font-size: 1.1rem; color: #fff; font-weight: 500;">
                            🥘 {ing}
                        </span>
                    </div>
                """, unsafe_allow_html=True)
            with c2:
                if st.button("🗑️", key=f"del_ing_{i}", help=f"Remove {ing}"):
                    st.session_state.ingredients.pop(i)
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Clear All Ingredients", use_container_width=True):
                st.session_state.ingredients.clear()
                st.rerun()
    else:
        st.info("✨ No ingredients added yet. Start typing above to add your first ingredient!")