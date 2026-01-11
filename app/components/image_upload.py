import streamlit as st
from PIL import Image
import io
from utils.image_predict import predict_image  # model predict function


def render_image_uploader():
    # Ensure keys exist
    st.session_state.setdefault("images", [])
    st.session_state.setdefault("uploader_key", 0)
    st.session_state.setdefault("uploader_files_sig", None)

    st.markdown(
    """
    <div class="section-title">
        <h3 style="font-size: 1.45rem;">Upload your individual ingredients</h3>
    </div>
    """,
    unsafe_allow_html=True,
)
    # --- FILE UPLOADER (ONLY FOR ADDING NEW IMAGES) ---
    uploaded = st.file_uploader(
        "Choose images",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed",
        help="Drag and drop or click to upload photos of your ingredients",
    )

    if uploaded:
        # Build a simple "signature" of the current uploader contents
        file_sig = [(f.name, getattr(f, "size", None)) for f in uploaded]

        # Only rebuild images if the uploader selection actually changed
        if st.session_state.uploader_files_sig != file_sig:
            new_images = []
            seen_files = set()  # <-- NEW: track (name, size) pairs

            for file in uploaded:
                key = (file.name, getattr(file, "size", None))
                if key in seen_files:
                    # skip exact duplicate files in this upload
                    continue
                seen_files.add(key)

                data = file.read()
                img_info = {"name": file.name, "bytes": data}

                # Run model prediction once per image
                try:
                    pil_img = Image.open(io.BytesIO(data))
                    pred = predict_image(pil_img)
                    img_info["prediction"] = pred
                except Exception:
                    img_info["prediction"] = None

                new_images.append(img_info)

            # Replace current images with this selection
            st.session_state.images = new_images
            st.session_state.uploader_files_sig = file_sig



    images = st.session_state.images

    # --- DISPLAY CURRENT IMAGES (SESSION STATE IS THE SOURCE OF TRUTH) ---
    if images:
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.1); 
                        padding: 1.25rem; 
                        border-radius: 16px; 
                        border: 1px solid rgba(255,255,255,0.2);
                        margin-top: 1.5rem;">
                <h4 style="color: #fff; margin-top: 0; margin-bottom: 1rem; font-size: 1.2rem;">
                    📸 Uploaded Photos ({len(images)})
                </h4>
            </div>
            """,
            unsafe_allow_html=True,
        )

        cols = st.columns(2)
        for idx, img_data in enumerate(images):
            with cols[idx % 2]:
                try:
                    pil_img = Image.open(io.BytesIO(img_data["bytes"]))
                    st.image(
                        pil_img,
                        caption=(
                            f"📷 {img_data['name']}"
                            + (
                                f"  •  🔍 {img_data['prediction']}"
                                if img_data.get("prediction")
                                else ""
                            )
                        ),
                        use_container_width=True,
                    )
                except Exception:
                    st.error(f"Could not display {img_data['name']}")

                # Per-image delete button – operates ONLY on session_state
                if st.button("🗑️ Remove", key=f"del_img_{idx}", use_container_width=True):
                    imgs = st.session_state.images
                    if 0 <= idx < len(imgs):
                        imgs.pop(idx)
                        st.session_state.images = imgs
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Clear-all button: also resets the uploader widget
        mid1, mid2, mid3 = st.columns([1, 2, 1])
        with mid2:
            if st.button("Clear All Photos", use_container_width=True):
                st.session_state.images = []
                st.session_state.uploader_key += 1  # forces a fresh uploader
                st.session_state.uploader_files_sig = None
                st.rerun()


    else:
        # No images at all → show friendly placeholder
        st.markdown(
            """
            <div style="background: rgba(255,255,255,0.05); 
                        padding: 2rem; 
                        border-radius: 16px; 
                        border: 2px dashed rgba(255,255,255,0.3);
                        text-align: center;
                        margin-top: 1rem;">
                <p style="color: rgba(255,255,255,0.7); font-size: 1.1rem; margin: 0;">
                    No photos uploaded yet<br>
                    <span style="font-size: 0.95rem;">Click or drag images above</span>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
