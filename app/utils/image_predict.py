# app/utils/image_predict.py

import os
import json
import torch
from PIL import Image
from torchvision import transforms
import timm

# -------------------------
# DEVICE
# -------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"

# -------------------------
# PATHS
# -------------------------
BASE_DIR = os.path.dirname(__file__)
LABEL_MAP_PATH = os.path.join(BASE_DIR, "..", "model", "label_map.json")
MODEL_PATH = os.path.join(BASE_DIR, "..", "model", "Food_Recognition_Model.pt")

# -------------------------
# LOAD LABEL MAP
# -------------------------
with open(LABEL_MAP_PATH, "r") as f:
    labels = json.load(f)

num_classes = len(labels)

# -------------------------
# REBUILD TRAINING MODEL
# -------------------------
model = timm.create_model(
    "efficientnet_b0",
    pretrained=False,          # IMPORTANT when loading custom weights
    num_classes=num_classes,
)

# -------------------------
# LOAD STATE DICT
# -------------------------
state_dict = torch.load(MODEL_PATH, map_location=device)
model.load_state_dict(state_dict)
model.to(device)
model.eval()

# -------------------------
# IMAGE TRANSFORM (same as training)
# -------------------------
IMG_SIZE = 224
test_transform = transforms.Compose([
    transforms.Lambda(lambda img: img.convert("RGB")),
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(
        (0.485, 0.456, 0.406),
        (0.229, 0.224, 0.225),
    ),
])

# -------------------------
# PREDICT
# -------------------------
def predict_image(image: Image.Image) -> str:
    img = image.convert("RGB")
    x = test_transform(img).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(x)
        pred_idx = outputs.argmax(1).item()

    return labels[pred_idx]
