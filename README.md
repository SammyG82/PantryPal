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
- 🌐 Web interface using Streamlit  

---

## 🧰 Tech Stack  

| Component | Technology |
|------------|-------------|
| **Frontend/UI** | Streamlit |
| **Image Recognition** | PyTorch (MobileNetV2 fine-tuned), OpenCV for image preprocessing |
| **Matching Logic** | Python, pandas, difflib, scikit-learn |
| **Nutrition API** | USDA FoodData Central API |
| **Deployment** | Streamlit Cloud / Heroku |
| **Version Control** | Git + GitHub (branches, issues, PRs) |

---

## 🧠 Workflow  

1. **User Input:**  
   - Text: `"tomato, onion, garlic"` and input is automatically formatted `"toMATo" -> "Tomato"`   
   - Image upload: Upload multiple images(max size 200 MB per image)
   - Any duplicate text entries or images will be automatically ignored
   - Straightforward "delete" button for each individual entry(image/text)
2. **Ingredient Normalization:**  
   - Converts “chopped tomato” → “tomato”
   - Performs image recognition and identifies each image(pic of tomato -> "tomato")
   - Maintains a list in the backend of each item entered(image/text)  
3. **Recipe Matching:**  
   - Uses the list created to find recipes with the highest overlap by running a search algorithm
   - Once all matches are made, each recipe is ranked by nutrition
4. **Filters & Nutrition:**  
   - Applies dietary filters and shows nutrition info  
5. **Output:**  
   - Sorted recipe list with match %, nutrition info, and tags (e.g., 🥦 Vegan, 💪 High Protein)  
   - Most nutritional at the top and least nutritional at the bottom

