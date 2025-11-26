import streamlit as st
from utils.helpers import process_uploaded_files
from PIL import Image
import io

from utils.image_predict import predict_image  # ⬅️ NEW


def render_image_uploader():
    st.markdown("""
        <div class="section-title">
            <span style="font-size: 1.8rem;">📸</span>
            <h3>Upload ingredient photos</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Create a visually appealing upload area
    uploaded = st.file_uploader(
        "Choose images",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed",
        help="📷 Drag and drop or click to upload photos of your ingredients"
    )
    
    if uploaded:
        # Process and store images
        st.session_state.images = []
        for file in uploaded:
            img_bytes = file.read()
            st.session_state.images.append({
                "name": file.name,
                "bytes": img_bytes
            })
        
        # Display uploaded images in a nice grid
        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.1); 
                        padding: 1.25rem; 
                        border-radius: 16px; 
                        border: 1px solid rgba(255,255,255,0.2);
                        margin-top: 1.5rem;">
                <h4 style="color: #fff; margin-top: 0; margin-bottom: 1rem; font-size: 1.2rem;">
                    📸 Uploaded Photos ({len(st.session_state.images)})
                </h4>
            </div>
        """, unsafe_allow_html=True)
        
        # Create a responsive grid for images
        cols = st.columns(2)
        for idx, img_data in enumerate(st.session_state.images):
            with cols[idx % 2]:
                with st.container():
                    st.markdown("""
                        <div class="preview-card">
                            <style>
                                .preview-card img {
                                    border-radius: 12px;
                                    width: 100%;
                                    height: auto;
                                }
                            </style>
                        </div>
                    """, unsafe_allow_html=True)

                    # Display the image
                    try:
                        image = Image.open(io.BytesIO(img_data["bytes"]))
                        st.image(
                            image,
                            caption=f"📷 {img_data['name']}",
                            use_container_width=True
                        )

                        # 🔮 NEW — RUN MODEL PREDICTION
                        try:
                            prediction = predict_image(image)
                            img_data["prediction"] = prediction  # store it

                            st.markdown(
                                f"<p><b>Detected ingredient:</b> {prediction}</p>",
                                unsafe_allow_html=True
                            )

                            # OPTIONAL: auto-add prediction to ingredients
                            if "ingredients" not in st.session_state:
                                st.session_state["ingredients"] = []
                            if prediction not in st.session_state["ingredients"]:
                                st.session_state["ingredients"].append(prediction)

                        except Exception as e:
                            st.caption(f"Prediction error: {e}")

                    except:
                        st.error(f"Could not display {img_data['name']}")

        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Clear button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Clear All Photos", use_container_width=True):
                st.session_state.images = []
                st.session_state.uploader_key += 1
                st.rerun()
    
    elif not st.session_state.images:
        # Show placeholder message when no images
        st.markdown("""
            <div style="background: rgba(255,255,255,0.05); 
                        padding: 2rem; 
                        border-radius: 16px; 
                        border: 2px dashed rgba(255,255,255,0.3);
                        text-align: center;
                        margin-top: 1rem;">
                <p style="color: rgba(255,255,255,0.7); font-size: 1.1rem; margin: 0;">
                    📸 No photos uploaded yet<br>
                    <span style="font-size: 0.95rem;">Click or drag images above</span>
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    # If images exist in session state but uploader is empty (after clear)
    elif st.session_state.images and not uploaded:
        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.1); 
                        padding: 1.25rem; 
                        border-radius: 16px; 
                        border: 1px solid rgba(255,255,255,0.2);
                        margin-top: 1.5rem;">
                <h4 style="color: #fff; margin-top: 0; margin-bottom: 1rem;">
                    📸 {len(st.session_state.images)} photo(s) ready
                </h4>
            </div>
        """, unsafe_allow_html=True)