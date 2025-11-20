import streamlit as st

# Session state helper keys
def _current_input_key() -> str:
    return f"ing_entry_{st.session_state.entry_key}"

def _get_current_text() -> str:
    return st.session_state.get(_current_input_key(), "").strip()

def _clear_text_input():
    st.session_state.entry_key += 1

# Ingredient helpers
def add_from_textbox():
    txt = _get_current_text()
    fix_case = txt.title().strip()
    st.session_state.ingredient_warning = None

    if fix_case in st.session_state.ingredients:
        st.session_state.ingredient_warning = f"'{fix_case}' has already been added!"
    else:
        st.session_state.ingredients.append(fix_case)
        _clear_text_input()

# Image helpers
def delete_image(idx: int):
    if 0 <= idx < len(st.session_state.images):
        st.session_state.images.pop(idx)

def process_uploaded_files(uploaded_files):
    if not uploaded_files:
        return
    existing_names = {img["name"] for img in st.session_state.images}
    duplicates = []

    for file_obj in uploaded_files:
        if file_obj.name not in existing_names:
            try:
                img_bytes = file_obj.read()
                st.session_state.images.append({
                    "name": file_obj.name,
                    "bytes": img_bytes,
                    "type": file_obj.type
                })
            except Exception as e:
                st.error(f"Error reading file {file_obj.name}: {str(e)}")
        else:
            duplicates.append(file_obj.name)

    if duplicates:
        if len(duplicates) == 1:
            st.error(f"This image already exists: {duplicates[0]}")
        else:
            st.error(f"These images already exist: {', '.join(duplicates)}")
