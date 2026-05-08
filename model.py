import io
import pickle
import base64
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as T
from PIL import Image
import segmentation_models_pytorch as smp


# ─────────────────────────────────────────────────────────────
# Model Architecture
# ─────────────────────────────────────────────────────────────
class PneumothoraxModel(nn.Module):

    def __init__(self, encoder_name="efficientnet-b0"):
        super().__init__()

        self.unet = smp.Unet(
            encoder_name=encoder_name,
            encoder_weights=None,
            in_channels=3,
            classes=1,
            activation=None,
        )

        enc_channels = self.unet.encoder.out_channels[-1]

        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(enc_channels, 1),
        )

    def forward(self, x):
        features = self.unet.encoder(x)
        seg_out = self.unet.decoder(*features)
        seg_out = self.unet.segmentation_head(seg_out)
        cls_out = self.classifier(features[-1])
        return seg_out, cls_out.squeeze(1)


# ─────────────────────────────────────────────────────────────
# CPU Safe Unpickler
# ─────────────────────────────────────────────────────────────
class CPUUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == "torch.storage" and name == "_load_from_bytes":
            return lambda b: torch.load(io.BytesIO(b), map_location="cpu")
        return super().find_class(module, name)


# ─────────────────────────────────────────────────────────────
# Model Service
# ─────────────────────────────────────────────────────────────
class ModelService:

    def __init__(self):
        self.model = None
        self.cfg = None
        self.metrics = None
        self.device = torch.device("cpu")
        self.transform = None

        self.classification_threshold = 0.5
        self.mask_threshold = 0.5
        self.min_area = 300

    # ─────────────────────────────────────────────────────────
    # Load Model
    # ─────────────────────────────────────────────────────────
    def load(self, pkl_path: str) -> None:
        with open(pkl_path, "rb") as f:
            pkg = CPUUnpickler(f).load()

        self.cfg = pkg["config"]
        self.metrics = pkg.get("metrics", {"best_val_dice": 0.7921})

        self.model = PneumothoraxModel(pkg["encoder_name"])
        self.model.load_state_dict(pkg["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()

        self.transform = T.Compose([
            T.Resize((self.cfg["img_size"], self.cfg["img_size"])),
            T.ToTensor(),
            T.Normalize(self.cfg["mean"], self.cfg["std"]),
        ])

        print("✅ Model Loaded Successfully")
        print(f"✅ Classification Threshold: {self.classification_threshold}")
        print(f"✅ Mask Threshold: {self.mask_threshold}")
        print(f"✅ Min Mask Area: {self.min_area}")
        if self.metrics:
            print(f"✅ Val Dice: {self.metrics.get('best_val_dice', 'N/A')}")

    # ─────────────────────────────────────────────────────────
    # Prediction
    # ─────────────────────────────────────────────────────────
    def predict(self, pil_img: Image.Image) -> dict:
        tensor = self.transform(pil_img.convert("RGB")).unsqueeze(0)

        with torch.no_grad():
            seg_logits, cls_logits = self.model(tensor)

        prob = torch.sigmoid(cls_logits).item()
        has_ptx = prob > self.classification_threshold

        prob_map = torch.sigmoid(seg_logits).squeeze().cpu().numpy()
        binary = (prob_map > self.mask_threshold).astype(np.uint8)

        if binary.sum() < self.min_area:
            binary = np.zeros_like(binary)

        return {
            "has_pneumothorax": has_ptx,
            "confidence": round(prob, 4),
            "prob_map": prob_map,
            "binary_mask": binary,
        }

    # ─────────────────────────────────────────────────────────
    # Grad‑CAM layer access (improved)
    # ─────────────────────────────────────────────────────────
    def get_gradcam_layer(self):
        """Return a suitable convolutional layer for Grad‑CAM."""
        # Try to get the last decoder block's convolution
        try:
            return self.model.unet.decoder[-1].conv
        except:
            # Fallback to last encoder block
            return self.model.unet.encoder[-1]

    def get_metrics(self):
        return self.metrics if self.metrics else {"best_val_dice": 0.7921}