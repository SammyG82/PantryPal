# 🥕 PantryPal  
### *Your Smart Recipe Recommender Based on What’s in Your Kitchen!*  

PantryPal is a web platform that suggests recipes based on the ingredients you already have — whether you **type them in** or **upload a photo** of your pantry.  
It uses **pretrained image recognition models** to detect ingredients and **fuzzy matching algorithms** to recommend the most relevant recipes, complete with **nutrition info** and **dietary filters**.

---

## 🧭 Project Overview  

> **Goal:** Suggest recipes based on typed ingredients or a photo of the user’s pantry.

### 🌟 Core Features  
- 📝 Text-based ingredient input  
- 🖼️ Image-based ingredient detection (CNN model)  
- 🧮 Fuzzy ingredient matching (e.g., `onions` ≈ `chopped onions`)  
- 🥗 Dietary filters: vegan, vegetarian, gluten-free  
- 🍎 Nutrition info integration via USDA FoodData Central API  
- 🌐 Web interface using Streamlit *(or Flask for advanced teams)*  

---

## 🧰 Tech Stack  

| Component | Technology |
|------------|-------------|
| **Frontend/UI** | Streamlit *(preferred)* or Flask |
| **Image Recognition** | TensorFlow / PyTorch (MobileNet, EfficientNet) |
| **Matching Logic** | Python, pandas, fuzzywuzzy, difflib, scikit-learn |
| **Nutrition API** | USDA FoodData Central API |
| **Deployment** | Streamlit Cloud / Heroku |
| **Version Control** | Git + GitHub (branches, issues, PRs) |

---

## 🧠 Example Workflow  

1. **User Input:**  
   - Text: `"tomato, onion, garlic"`  
   - or upload a pantry image  
2. **Ingredient Normalization:**  
   - Converts “chopped tomato” → “tomato”  
3. **Recipe Matching:**  
   - Finds recipes with highest overlap  
4. **Filters & Nutrition:**  
   - Applies dietary filters and shows nutrition info  
5. **Output:**  
   - Sorted recipe list with match %, nutrition info, and tags (e.g., 🥦 Vegan, 💪 High Protein)  

