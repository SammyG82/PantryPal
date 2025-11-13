
import streamlit as st
from io import BytesIO

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="PantryPal", page_icon="🥕", layout="wide")

# ------------------ SESSION STATE ------------------
defaults = {
    "ingredients": [],
    "images": [],  # Now stores dicts with {name, bytes, type}
    "uploader_key": 0,
    "entry_key": 0,
    "cooked": False,  # Track if user clicked Cook button
}

for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ------------------ GLOBAL STYLES ------------------
st.markdown("""
<style>
.header-wrap {text-align:center; margin-top:0.5rem; margin-bottom:1.25rem;}
.header-wrap h1 {font-size: 2.6rem; line-height: 1.1; margin: 0 0 0.5rem 0;}
.lead {font-size: 1.12rem; line-height: 1.75; margin: 0.25rem 0 0.75rem;}
.lead b {font-weight: 700;}
.callout {
  margin: 0 auto 1.25rem; max-width: 900px; padding: 1rem 1.25rem;
  border: 1px solid rgba(255,255,255,0.08); border-radius: 14px;
  background: rgba(255,255,255,0.03);
}
.callout ul {margin: 0.25rem 0 0.75rem 1.2rem;}
.callout li {margin: 0.25rem 0;}
.section-title {display:flex; align-items:center; gap:.5rem;}
.stButton>button {height: 42px; border-radius: 12px; font-weight: 600;}
.preview-card {
  padding: .5rem; border: 1px solid rgba(255,255,255,.08);
  border-radius: 12px; background: rgba(255,255,255,.02);
}
</style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.markdown(
    """
    <div class="header-wrap">
      <h1>🥕 PantryPal</h1>
    </div>
    <div class="callout">
      <p class="lead">
        <b>Welcome to PantryPal!</b> Not sure what to cook? <b>We've got you covered.</b>
      </p>
      <p class="lead"><b>You can either:</b></p>
      <ul>
        <li><b>Upload photos</b> of the ingredients you have</li>
        <li><b>Type</b> your ingredients in the box</li>
      </ul>
      <p class="lead">
        Hit <b>Cook</b> when you're done and we'll show recipes from <b>Healthiest → Cheat Day</b> 🎉
      </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ------------------ HELPERS ------------------
def _current_input_key() -> str:
    return f"ing_entry_{st.session_state.entry_key}"

def _get_current_text() -> str:
    return st.session_state.get(_current_input_key(), "").strip()

def _clear_text_input():
    st.session_state.entry_key += 1

def add_from_textbox():
    txt = _get_current_text()

    fix_case = txt.title().strip()
    st.session_state.ingredient_warning = None

    # Check for duplicate
    if fix_case in st.session_state.ingredients:
        st.session_state.ingredient_warning = f"'{fix_case}' has already been added!"
    else:
        st.session_state.ingredients.append(fix_case)
    
    _clear_text_input()  # clear input key for next entry

def delete_image(idx: int):
    st.session_state.images.pop(idx)
    st.session_state.uploader_key += 1

# ------------------ MAIN LAYOUT ------------------
left, right = st.columns(2, gap="large")

# ---- LEFT: IMAGES ----
with left:
    st.markdown('<div class="section-title">📸 <h3>Upload ingredient photos</h3></div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload images",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
        help="Drag & drop or browse. Supported: PNG, JPG, JPEG"
    )

    # Convert uploaded files to bytes for persistence
    if uploaded:
        existing_names = {img["name"] for img in st.session_state.images}
        for f in uploaded:
            if f.name not in existing_names:
                # Read file bytes and store
                img_bytes = f.read()
                st.session_state.images.append({
                    "name": f.name,
                    "bytes": img_bytes,
                    "type": f.type
                })

    # Preview list
    if st.session_state.images:
        st.write("**Added photos:**")
        for i, img in enumerate(st.session_state.images):
            c1, c2 = st.columns([7, 1])
            with c1:
                with st.container(border=False):
                    st.markdown('<div class="preview-card">', unsafe_allow_html=True)
                    st.image(img["bytes"], caption=img["name"], use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                st.write("")
                if st.button("❌", key=f"del_img_{i}"):
                    delete_image(i)
                    st.rerun()
    else:
        st.info("No photos added yet.")

# ---- RIGHT: TEXT INGREDIENTS ----
with right:
    st.markdown('<div class="section-title">✍️ <h3>Type your ingredients</h3></div>', unsafe_allow_html=True)

    st.text_input(
        "Enter individual ingredient:",
        placeholder="e.g., Onion",
        key=_current_input_key(),
        on_change=add_from_textbox,
    )

    # Display the warning immediately under the text box
    if st.session_state.get("ingredient_warning"):
        st.warning(st.session_state.ingredient_warning)

    if st.button("Add"):
    # Get the current text from the text_input
        txt = _get_current_text().strip()
        if not txt:
            st.warning("Please input an ingredient")    
        else:
            add_from_textbox()  # This will handle duplicates and add the ingredient
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

# ---- COOK BUTTON ----
st.divider()
if st.button("🍳 Cook!", use_container_width=True):
    if not st.session_state.images and not st.session_state.ingredients:
        st.error("⚠️ Please add at least one ingredient or photo before cooking!")
    else:
        st.session_state.cooked = True  # Mark as cooked
        st.switch_page("pages/Results.py")