import streamlit as st
from utils.helpers import process_uploaded_files, delete_image

def render_image_uploader():
    st.markdown('<div class="section-title">📸 <h3>Upload ingredient photos</h3></div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload images",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
        help="Drag & drop or browse. Supported: PNG, JPG, JPEG"
    )

    if uploaded:
        process_uploaded_files(uploaded)
        st.session_state.uploader_key += 1
        st.rerun()

    # Preview uploaded images
    if st.session_state.images:
        st.write("**Added photos:**")
        for i, img in enumerate(st.session_state.images):
            col1, col2 = st.columns([7, 1])
            with col1:
                st.markdown('<div class="preview-card">', unsafe_allow_html=True)
                try:
                    st.image(img["bytes"], caption=img["name"], use_container_width=True)
                except Exception as e:
                    st.error(f"Error displaying image {img['name']}: {str(e)}")
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                st.write("")
                if st.button("❌", key=f"del_img_{i}", help=f"Remove {img['name']}"):
                    delete_image(i)
                    st.rerun()
    else:
        st.info("No photos added yet. Upload some ingredient photos above!")
