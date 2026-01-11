import streamlit as st

def render_cook_button():
    st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
    st.divider()
    st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
    
    # Create centered columns for the button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Add an animated container for the button
        st.markdown("""
            <div style="text-align: center; margin: 1rem 0;">
                <style>
                    @keyframes glow {
                        0% { box-shadow: 0 0 5px rgba(245,87,108,0.5); }
                        50% { box-shadow: 0 0 20px rgba(245,87,108,0.8), 0 0 30px rgba(245,87,108,0.6); }
                        100% { box-shadow: 0 0 5px rgba(245,87,108,0.5); }
                    }
                    .cook-button-container {
                        animation: glow 2s ease-in-out infinite;
                        border-radius: 20px;
                        padding: 0.5rem;
                    }
                </style>
                <div class="cook-button-container">
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("**COOK!**", use_container_width=True, type="primary"):
            if not st.session_state.images and not st.session_state.ingredients:
                st.error("Please add at least one ingredient or photo before cooking!")
            else:
                with st.spinner("Finding amazing recipes for you..."):
                    import time
                    time.sleep(0.5)

                    # ---- Build combined ingredient list for searching ----
                    base_ings = list(st.session_state.get("ingredients", []))

                    image_ings = []
                    for img in st.session_state.get("images", []):
                        pred = (img.get("prediction") or "").strip()
                        if pred:
                            image_ings.append(pred)

                    # Merge + dedupe while preserving order
                    combined = []
                    seen = set()
                    for item in base_ings + image_ings:
                        norm = item.strip()
                        if not norm:
                            continue
                        key = norm.lower()
                        if key not in seen:
                            seen.add(key)
                            combined.append(norm)

                    st.session_state.all_ingredients = combined
                    st.session_state.cooked = True
                    st.switch_page("pages/Results.py")

    
    st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing