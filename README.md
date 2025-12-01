# 🥕 PantryPal  
### *Your Smart Recipe Recommender Based on What’s in Your Kitchen!*  

PantryPal is a web app that suggests recipes based on the ingredients you already have — whether you **type them in** or **upload a photo** of your pantry.  
It uses **pretrained image recognition models** to detect ingredients and **fuzzy matching algorithms** to recommend the most relevant recipes, complete with **nutrition info**.
---

## 🧭 Project Overview  

> **Goal:** Recommend recipes using a combination of text input, image recognition, and smart fuzzy ingredient matching.

### Core Features  
- Text-based ingredient input  
- Image-based ingredient detection (MobileNetV3)  
- Fuzzy ingredient matching (e.g., `chopped onions` ≈ `onions`)  
- Fuzzy recipe matching based on overlap score
- Nutrition based ranking
- Duplicate image/text handling & simple delete actions
- Web interface using Streamlit  

---

## Tech Stack  

| Component | Technology |
|------------|-------------|
| **Frontend/UI** | Streamlit |
| **Image Recognition** | PyTorch (MobileNetV3 fine-tuned), OpenCV for image preprocessing |
| **Pre Processing** | Pillow (PIL), NumPy |
| **Matching Logic** | Python, pandas, rapidfuzz difflib, scikit-learn |
| **Deployment** | Streamlit Cloud |
| **Version Control** | Git + GitHub (branches, issues, PRs) |

---

## 🧠 Workflow  

1. **User Input:**  
   - Add text ingredients
   - Upload multiple images (max 200MB each)
   - Duplicate items (img/text) automatically ignored
   - Each item has a delete button in the UI
2. **Ingredient Normalization:**  
   - Text cleanup “chopped tomato” → “tomato”
   - CNN image inference (MobileNetV3 → ingredient label)
   - Maintains a unified backend list of all detected/typed items
3. **Recipe Matching:**  
   - Searches through recipes.csv
   - Computes fuzzy similarity for each ingredient
   - Calculates match score + nutrition score
4. **Ranking & Display:**  
   - Recipes sorted by match % and nutrition
   - Displays key details; score breakdown and link to recipe




```
PantryPal/
├── app/                                  # Main Streamlit application
│   ├── components/                       # Reusable UI building blocks
│   │   ├── cook_button.py                # "Cook!" CTA button component
│   │   ├── image_upload.py               # Image upload component
│   │   └── ingredient_input.py           # Text input component for ingredients
│   │
│   ├── model/                            # Image recognition model assets
│   │   ├── Food_Recognition_Model.pt     # Trained MobileNetV3 model
│   │   └── label_map.json                # Maps model outputs → ingredient names
│   │
│   ├── pages/
│   │   └── Results.py                    # Results and recipe display page
│   │
│   ├── utils/                            # Backend logic & helper functions
│   │   ├── helpers.py                    # General utils (normalization, cleaning)
│   │   ├── image_predict.py              # CNN inference for image uploads
│   │   ├── Home.py                       # Streamlit home routing
│   │   └── styles.py                     # CSS + UI styling utilities
│
├── data/
│   ├── cleaned/                          # Cleaned datasets (future use)
│   └── raw/
│       └── recipes.csv                   # Main recipe dataset (ingredients + nutrition)
│
├── models/
│   └── mobilenet_head.pt                 # Additional model head weights (if used)
│
├── notebooks/
│   └── dataset_exploration.ipynb         # Exploratory analysis notebook
│
├── scripts/
│   └── recipe_search.py                  # Fuzzy matching + ranking algorithm
│
├── venv/                                 # Virtual environment (ignored in repo)
├── requirements.txt                      # Python dependencies
├── .gitignore                            # Git ignore rules
└── README.md                             # Project documentation
```