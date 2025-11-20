# styles.py
def apply_styles():
    import streamlit as st
    st.markdown("""
    <style>
    /* ---------- HOME PAGE HEADER ---------- */
    .header-wrap {
        text-align: center;
        margin-top: 1rem;
        margin-bottom: 1.25rem;
    }
    .header-wrap h1 {
        font-size: 2.6rem;
        line-height: 1.1;
        margin: 0 0 0.5rem 0;
    }

    /* ---------- HOME PAGE / GENERAL ---------- */
    .lead {
        font-size: 1.12rem;
        line-height: 1.75;
        margin: 0.25rem 0 0.75rem;
    }
    .lead b { font-weight: 700; }
    .callout {
        margin: 0 auto 1.25rem;
        max-width: 900px;
        padding: 1rem 1.25rem;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        background: rgba(255,255,255,0.03);
    }
    .callout ul { margin: 0.25rem 0 0.75rem 1.2rem; }
    .callout li { margin: 0.25rem 0; }
    .section-title {
        display:flex;
        align-items:center;
        gap:.5rem;
    }
    .stButton>button {
        height: 42px;
        border-radius: 12px;
        font-weight: 600;
    }

    /* ---------- IMAGE PREVIEW CARDS ---------- */
    .preview-card {
        padding: .5rem;
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 12px;
        background: rgba(255,255,255,.02);
    }

    /* ---------- RESULTS PAGE INGREDIENT BADGES ---------- */
    .result-ingredient {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        margin: 0.25rem;
        border-radius: 12px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)
