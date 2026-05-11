# backend/utils/image_predict.py

import json
import logging
from pathlib import Path
import warnings
import torch
import torch.nn as nn
import torch.nn.functional as F
import open_clip
from PIL import Image
from torchvision import transforms

logger = logging.getLogger(__name__)

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
# CONSTANTS
# -------------------------
HF_REPO = "SammyG82/Single_Ingredient_Identification"
MODEL_DIR = BASE_DIR / "model"
LABEL_MAP_PATH = MODEL_DIR / "label_map.json"
MODEL_PATH = MODEL_DIR / "Food_Recognition_Model_94.pt"

CLIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
CLIP_STD = (0.26862954, 0.26130258, 0.27577711)
IMG_SIZE = 224

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

    def encode_image(self, x):
        return F.normalize(self.encoder(x), dim=-1)

    def forward(self, x):
        feats = self.encode_image(x)
        logits = self.head(feats)
        return logits, feats

# -------------------------
# LAZY STATE
# -------------------------
_model: CLIPIngredientClassifier | None = None
_transform = None
_labels: dict | None = None


def _ensure_model_files() -> None:
    from huggingface_hub import hf_hub_download
    for filename in ["Food_Recognition_Model_94.pt", "label_map.json"]:
        dest = MODEL_DIR / filename
        if not dest.exists():
            logger.info("Downloading %s from HuggingFace...", filename)
            hf_hub_download(
                repo_id=HF_REPO,
                filename=filename,
                local_dir=str(MODEL_DIR),
            )
            logger.info("Downloaded %s", filename)


def load_model() -> None:
    global _model, _transform, _labels
    if _model is not None:
        return

    _ensure_model_files()

    with open(LABEL_MAP_PATH, "r") as f:
        _labels = json.load(f)

    num_classes = len(_labels)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="QuickGELU mismatch", category=UserWarning)
        clip_model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
    m = CLIPIngredientClassifier(clip_model, num_classes).to(device)
    m.load_state_dict(torch.load(MODEL_PATH, map_location=device, weights_only=True), strict=False)
    m.eval()
    _model = m
    _transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(CLIP_MEAN, CLIP_STD),
    ])


# -------------------------
# PREDICT
# -------------------------
def predict_image(image: Image.Image) -> str:
    load_model()
    if _model is None or _transform is None or _labels is None:
        raise RuntimeError("Model not loaded — call load_model() first")

    x = _transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        logits, _ = _model(x)
        pred_idx = logits.argmax(1).item()

    label = _labels.get(str(pred_idx))
    if label is None:
        raise ValueError(f"Model predicted class {pred_idx} not in label map (size {len(_labels)})")
    return label
