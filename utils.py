import io, base64
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

def make_overlay(pil_img: Image.Image, binary: np.ndarray) -> str:
    img = np.array(pil_img.convert("RGB").resize((256, 256)))
    out = img.copy()
    mask = binary.astype(bool)
    out[mask, 0] = np.clip(out[mask, 0] + 120, 0, 255)
    out[mask, 1] = (out[mask, 1] * 0.3).astype(np.uint8)
    out[mask, 2] = (out[mask, 2] * 0.3).astype(np.uint8)
    return _pil_to_b64(Image.fromarray(out))

def make_heatmap(prob_map: np.ndarray) -> str:
    fig, ax = plt.subplots(figsize=(3, 3), dpi=90)
    ax.imshow(prob_map, cmap="RdYlBu_r", vmin=0, vmax=1)
    ax.axis("off")
    fig.tight_layout(pad=0)
    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    buf = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8).reshape(h, w, 3)
    plt.close(fig)
    return _pil_to_b64(Image.fromarray(buf))

def _pil_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

# ========== SEVERITY CALCULATION (NEW) ==========
def calculate_severity(binary_mask: np.ndarray) -> dict:
    """
    Calculate pneumothorax severity from binary segmentation mask.
    Returns dict with: percentage, level, color, description.
    """
    if binary_mask is None or binary_mask.size == 0:
        return {"percentage": 0, "level": "None", "color": "gray", "description": "No pneumothorax detected"}
    
    total_pixels = binary_mask.size
    positive_pixels = np.sum(binary_mask)
    percentage = (positive_pixels / total_pixels) * 100
    
    if percentage < 15:
        level = "Mild"
        color = "#f59e0b"  # yellow
        description = f"Small pneumothorax ({percentage:.1f}%) – often managed conservatively."
    elif percentage < 30:
        level = "Moderate"
        color = "#ef4444"  # red
        description = f"Moderate collapse ({percentage:.1f}%) – may require needle aspiration."
    else:
        level = "Severe"
        color = "#b91c1c"  # dark red
        description = f"Large pneumothorax ({percentage:.1f}%) – chest tube likely needed."
    
    return {
        "percentage": round(percentage, 1),
        "level": level,
        "color": color,
        "description": description
    }