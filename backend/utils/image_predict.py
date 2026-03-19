# backend/utils/image_predict.py

import json
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import open_clip
from pathlib import Path
from PIL import Image
from torchvision import transforms

# -------------------------
# DEVICE
# -------------------------
if torch.backends.mps.is_available():
    device = "mps"
elif torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

# -------------------------
# PATHS — relative to backend/ directory
# -------------------------
BASE_DIR = Path(__file__).parent.parent

# -------------------------
# DOWNLOAD MODEL FROM HUGGINGFACE IF NOT PRESENT
# -------------------------
HF_REPO = "SammyG82/Single_Ingredient_Identification"
HF_TOKEN = os.environ.get("HF_TOKEN")
MODEL_DIR = BASE_DIR / "model"

def _ensure_model_files():
    from huggingface_hub import hf_hub_download
    for filename in ["Food_Recognition_Model_94.pt", "label_map.json"]:
        dest = MODEL_DIR / filename
        if not dest.exists():
            print(f"Downloading {filename} from HuggingFace...")
            hf_hub_download(
                repo_id=HF_REPO,
                filename=filename,
                local_dir=str(MODEL_DIR),
                token=HF_TOKEN,
            )
            print(f"Downloaded {filename}")

_ensure_model_files()
LABEL_MAP_PATH = BASE_DIR / "model" / "label_map.json"
MODEL_PATH = BASE_DIR / "model" / "Food_Recognition_Model_94.pt"

# -------------------------
# LOAD LABELS
# -------------------------
with open(LABEL_MAP_PATH, "r") as f:
    labels = json.load(f)  # {"0": "apple", "1": "banana", ...}

num_classes = len(labels)

# -------------------------
# MODEL ARCHITECTURE
# -------------------------
class CLIPIngredientClassifier(nn.Module):
    def __init__(self, clip_model, num_classes, embed_dim=512):
        super().__init__()
        self.encoder = clip_model.visual
        self.head = nn.Sequential(
            nn.LayerNorm(embed_dim),
            nn.Dropout(0.2),
            nn.Linear(embed_dim, num_classes),
        )
        self.logit_scale = nn.Parameter(torch.ones([]) * torch.log(torch.tensor(1 / 0.07)))

    def encode_image(self, x):
        return F.normalize(self.encoder(x), dim=-1)

    def forward(self, x):
        feats = self.encode_image(x)
        logits = self.head(feats)
        return logits, feats

# -------------------------
# BUILD & LOAD MODEL
# -------------------------
clip_model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
model = CLIPIngredientClassifier(clip_model, num_classes).to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()

# -------------------------
# IMAGE TRANSFORM (matches training test_tf)
# -------------------------
CLIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
CLIP_STD = (0.26862954, 0.26130258, 0.27577711)
IMG_SIZE = 224

test_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(CLIP_MEAN, CLIP_STD),
])

# -------------------------
# PREDICT
# -------------------------
def predict_image(image: Image.Image) -> str:
    img = image.convert("RGB")
    x = test_transform(img).unsqueeze(0).to(device)

    with torch.no_grad():
        logits, _ = model(x)
        pred_idx = logits.argmax(1).item()

    return labels[str(pred_idx)]
