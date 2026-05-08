# interpretability.py - Robust Grad‑CAM with fallback
import torch
import torch.nn.functional as F
import numpy as np
import io
import base64
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()
        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()
        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_backward_hook(backward_hook)

    def generate(self, input_tensor, class_idx=None):
        self.model.zero_grad()
        seg_logits, cls_logits = self.model(input_tensor)
        if class_idx is None:
            prob = torch.sigmoid(cls_logits).item()
            class_idx = 1 if prob > 0.5 else 0
        score = cls_logits[0] if class_idx == 1 else -cls_logits[0]
        self.model.zero_grad()
        score.backward()

        gradients = self.gradients[0]      # [C, H, W]
        activations = self.activations[0]  # [C, H, W]
        weights = torch.mean(gradients, dim=(1, 2))
        cam = torch.zeros(activations.shape[1:], dtype=torch.float32)
        for i, w in enumerate(weights):
            cam += w * activations[i]
        cam = F.relu(cam)
        cam = cam.cpu().numpy()
        if cam.max() - cam.min() > 1e-8:
            cam = (cam - cam.min()) / (cam.max() - cam.min())
        else:
            cam = np.zeros_like(cam)
        return cam

def overlay_gradcam(pil_img, cam, alpha=0.4):
    try:
        img = np.array(pil_img.convert("RGB").resize((256, 256)))
        cam_resized = np.array(Image.fromarray((cam * 255).astype(np.uint8)).resize((256, 256), Image.BILINEAR)) / 255.0
        norm = Normalize(vmin=0, vmax=1)
        cmap = plt.cm.jet
        heatmap = cmap(norm(cam_resized))[:, :, :3]
        heatmap = (heatmap * 255).astype(np.uint8)
        overlay = (img * (1 - alpha) + heatmap * alpha).astype(np.uint8)
        return Image.fromarray(overlay)
    except Exception as e:
        print(f"overlay_gradcam error: {e}")
        return Image.new('RGB', (256, 256), color='gray')

def _pil_to_b64(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def reliability_badge(confidence, mask_area, mask_threshold=300):
    if confidence > 0.85 and mask_area > mask_threshold:
        level = "High"
        color = "#10b981"
        desc = "Strong AI confidence and clear segmentation. High reliability."
    elif confidence > 0.7 and mask_area > mask_threshold/2:
        level = "Moderate"
        color = "#f59e0b"
        desc = "Moderate confidence. Consider clinical correlation."
    else:
        level = "Low"
        color = "#ef4444"
        desc = "Low confidence or unclear finding. Manual review recommended."
    return {"level": level, "color": color, "description": desc}