# PantryPal
---

## Project Overview  

> **Goal:** Create a web app that suggests recipes based on the ingredients users already have. Users can either *type them in* or *upload a photo* of the ingredients in their pantry. It uses a *fine-tuned convolutional neural network (EfficientNetB0)* for image-based individual ingredient detection and *fuzzy string matching* to recommend and rank recipes based on *ingredient overlap* and *available nutrition metadata*.


---

## Tech Stack  

| Component | Technology |
|------------|-------------|
| **Frontend/UI** | Streamlit |
| **Image Recognition** | PyTorch (EfficientNetB0 fine-tuned) |
| **Pre Processing** | Pillow (PIL), NumPy |
| **Matching Logic** | Python, pandas, rapidfuzz |
| **Deployment** | Streamlit Cloud |
| **Version Control** | Git + GitHub (branches, issues, PRs) |

---

## Core Features  
- Text-based ingredient input  
- Image-based individual ingredient detection
- Fuzzy ingredient matching (e.g., `chopped onions` ≈ `onions`)  
- Recipe ranking based on ingredient overlap score
- Secondary ranking based on available nutrition fields (e.g., calories or macros, if present)
- Duplicate ingredient detection using normalized text comparisons
- Web interface using Streamlit  

---

## Workflow  

1. **User Input:**  
   - Add text ingredients
   - Upload ingredient image(s) (subject to Streamlit upload limits)
   - Duplicate items (img/text) automatically ignored
   - Each item has a delete button in the UI
2. **Ingredient Normalization:**  
   - Text cleanup “chopped tomato” → “tomato”
   - CNN image inference (EfficientNetB0 → ingredient label)
   - Maintains a unified backend list of all detected/typed items
3. **Recipe Matching:**  
   - Searches through recipes.csv
   - Computes fuzzy similarity for each ingredient
   - Calculates an ingredient match score and incorporates available nutrition metadata
4. **Ranking & Display:**  
   - Recipes sorted/ranked by ingredient match % and nutrition metadata
   - Displays key details; score breakdown and link to recipe

---

## Project Structure

```
PantryPal/
├── app/                                  # Main Streamlit application
│   ├── components/                       # Reusable UI building blocks
│   │   ├── cook_button.py                # "Cook!" CTA button component
│   │   ├── image_upload.py               # Image upload component
│   │   └── ingredient_input.py           # Text input component for ingredients
│   │
│   ├── model/                            # Image recognition model assets
│   │   ├── Food_Recognition_Model.pt     # Trained EfficientNetB0 model
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