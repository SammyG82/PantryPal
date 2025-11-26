# styles.py
def apply_styles():
    import streamlit as st
    st.markdown("""
    <style>
    /* ---------- GLOBAL STYLES ---------- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main app background */
    .stApp {
        background: linear-gradient(135deg, #0a1a2f 0%, #0f2745 100%);
    }

                
    
    /* ---------- HOME PAGE HEADER ---------- */
    .header-wrap {
        text-align: center;
        margin-top: 2rem;
        margin-bottom: 2rem;
    }
    .header-wrap h1 {
        font-size: 3.5rem;
        font-weight: 800;
        line-height: 1.1;
        margin: 0 0 1rem 0;
        background: linear-gradient(135deg, #fff 0%, #f0f0f0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }

    /* ---------- CALLOUT BOX ---------- */
    .callout {
        margin: 0 auto 2rem;
        max-width: 900px;
        padding: 2rem 2.5rem;
        border: 2px solid rgba(255,255,255,0.2);
        border-radius: 24px;
        background: rgba(255,255,255,0.15);
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    .callout:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.25);
        background: rgba(255,255,255,0.18);
    }
    .callout p {
        color: #fff;
        font-size: 1.2rem;
        line-height: 1.8;
        margin: 0.5rem 0;
    }
    .callout ul {
        margin: 1rem 0 1rem 1.5rem;
        color: #fff;
        font-size: 1.15rem;
        line-height: 2;
    }
    .callout li {
        margin: 0.5rem 0;
    }
    .callout b {
        font-weight: 700;
        color: #ffd700;
        text-shadow: 0 0 10px rgba(255,215,0,0.3);
    }

    /* ---------- SECTION TITLES ---------- */
    .section-title {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
        padding: 1rem 1.5rem;
        background: rgba(255,255,255,0.1);
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .section-title h3 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
        color: #fff;
    }

    /* ---------- BUTTONS ---------- */
    .stButton > button {
        height: auto;
        padding: 0.75rem 2rem;
        border-radius: 16px;
        font-weight: 600;
        font-size: 1.1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: 2px solid rgba(255,255,255,0.3);
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Cook button - make it extra prominent */
    div[data-testid="column"]:has(button:contains("Cook")) > div > div > div > button,
    button:has-text("🍳 Cook!") {
        height: 80px !important;
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
        border: 3px solid rgba(255,255,255,0.4) !important;
        box-shadow: 0 8px 25px rgba(245,87,108,0.4) !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 8px 25px rgba(245,87,108,0.4); }
        50% { box-shadow: 0 8px 35px rgba(245,87,108,0.6); }
        100% { box-shadow: 0 8px 25px rgba(245,87,108,0.4); }
    }

    /* ---------- INPUT FIELDS ---------- */
    .stTextInput > div > div > input {
        padding: 0.75rem 1rem;
        border-radius: 12px;
        border: 2px solid rgba(255,255,255,0.3);
        background: rgba(255,255,255,0.95);
        color: #000 !important;  /* Black text for visibility */
        font-size: 1.1rem;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input::placeholder {
        color: #666 !important;  /* Gray placeholder text */
    }
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.2);
        background: #fff;
        color: #000 !important;
    }

    /* ---------- IMAGE UPLOAD AREA ---------- */
    section[data-testid="stFileUploadDropzone"] {
        background: rgba(255,255,255,0.1);
        border: 3px dashed rgba(255,255,255,0.4);
        border-radius: 20px;
        transition: all 0.3s ease;
    }
    section[data-testid="stFileUploadDropzone"]:hover {
        background: rgba(255,255,255,0.15);
        border-color: rgba(255,255,255,0.6);
        transform: scale(1.02);
    }
    section[data-testid="stFileUploadDropzone"] > div {
        color: #fff;
        font-weight: 600;
    }

    /* ---------- IMAGE PREVIEW CARDS ---------- */
    .preview-card {
        padding: 1rem;
        border: 2px solid rgba(255,255,255,0.3);
        border-radius: 20px;
        background: rgba(255,255,255,0.15);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        margin-bottom: 1rem;
    }
    .preview-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
        background: rgba(255,255,255,0.2);
    }

    /* ---------- EXPANDER ---------- */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.1);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.2);
        font-weight: 600;
        font-size: 1.1rem;
    }
    div[data-testid="stExpander"] > details {
        border: none;
        background: rgba(255,255,255,0.05);
        border-radius: 16px;
    }

    /* ---------- ALERTS & INFO BOXES ---------- */
    .stAlert {
        padding: 1rem 1.5rem;
        border-radius: 16px;
        border: 2px solid;
        font-weight: 500;
        backdrop-filter: blur(5px);
        width: 100%;  /* Full width to prevent squishing */
        margin: 0.5rem 0;
    }
    div[data-testid="stAlert"][data-baseweb="notification"] {
        background: rgba(255,255,255,0.15);
    }
    
    /* Warning messages */
    .stWarning, div[data-testid="stWarning"] {
        background: rgba(255,193,7,0.15) !important;
        border: 2px solid rgba(255,193,7,0.3) !important;
        color: #fff !important;
    }

    /* ---------- DIVIDERS ---------- */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    }

    /* ---------- INGREDIENT LIST ---------- */
    div:has(> div > p:contains("Ingredients added:")) {
        background: rgba(255,255,255,0.08);
        padding: 1rem;
        border-radius: 16px;
        margin-top: 1rem;
    }
    
    /* Small delete buttons */
    button[key^="del_ing_"] {
        background: rgba(244,67,54,0.8) !important;
        padding: 0.25rem 0.5rem !important;
        min-height: 30px !important;
        font-size: 0.9rem !important;
    }
    button[key^="del_ing_"]:hover {
        background: rgba(244,67,54,1) !important;
    }

    /* ---------- RECIPE CARDS (Results Page) ---------- */
    .recipe-card {
        margin: 1rem 0;
        padding: 1.5rem 1.75rem;
        border: 2px solid rgba(255,255,255,0.2);
        border-radius: 20px;
        background: rgba(255,255,255,0.15);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    .recipe-card:hover {
        transform: translateX(5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        background: rgba(255,255,255,0.2);
    }
    .recipe-card h3 {
        margin: 0 0 0.75rem 0;
        font-size: 1.5rem;
        font-weight: 700;
        color: #fff;
    }
    .recipe-card p {
        margin: 0.5rem 0;
        color: rgba(255,255,255,0.9);
        font-size: 1.05rem;
    }
    
    /* Health badges */
    .health-badge {
        display: inline-block;
        padding: 0.35rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        margin-left: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .badge-healthy {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%);
        color: #fff;
        box-shadow: 0 2px 8px rgba(86,171,47,0.3);
    }
    .badge-balanced {
        background: linear-gradient(135deg, #f2994a 0%, #f2c94c 100%);
        color: #fff;
        box-shadow: 0 2px 8px rgba(242,153,74,0.3);
    }
    .badge-cheat {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        color: #fff;
        box-shadow: 0 2px 8px rgba(235,51,73,0.3);
    }
    
    .muted {
        color: rgba(255,255,255,0.6);
        font-size: 0.95rem;
        font-style: italic;
    }

    /* ---------- COLUMNS SPACING ---------- */
    div[data-testid="column"] {
        padding: 0 0.5rem;
    }
    
    /* ---------- SUBHEADERS ---------- */
    .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: #fff;
        font-weight: 700;
    }
    
    /* ---------- SUCCESS/ERROR MESSAGES ---------- */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 12px;
        font-weight: 600;
    }
    
    /* ---------- METRIC STYLING ---------- */
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.1);
        padding: 1rem;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* ---------- TEXT COLOR FIX ---------- */
    p, li, span, div {
        color: #fff;
    }
    
    /* Back/Clear buttons special styling */
    button:has-text("Back to Home"),
    button:has-text("Clear") {
        background: rgba(255,255,255,0.2) !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
    }
    button:has-text("Back to Home"):hover,
    button:has-text("Clear"):hover {
        background: rgba(255,255,255,0.3) !important;
    }
    
    </style>
    """, unsafe_allow_html=True)