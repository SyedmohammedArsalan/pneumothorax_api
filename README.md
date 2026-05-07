# 🫁 PneumoAI: End-to-End Pneumothorax Detection API

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-05998B?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1.0-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent medical imaging API that leverages **Deep Learning** to detect and segment Pneumothorax (collapsed lung) from Chest X-Rays. Built with a custom **U-Net + EfficientNet-B0** architecture.

---

## 📖 Table of Contents
- [Project Overview](#project-overview)
- [Architecture Details](#architecture-details)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Threshold Configuration](#threshold-configuration)

---

## 🧐 Project Overview
Pneumothorax is a critical condition where air leaks into the space between the lung and chest wall. Early detection is vital. This project provides:
1. **Classification:** A binary verdict with a confidence score.
2. **Segmentation:** A high-resolution mask showing the exact location of the collapse.

---

## 🏗️ Architecture Details
The model uses **Segmentation Models PyTorch (SMP)** with the following configuration:
* **Backbone:** EfficientNet-B0 (Pre-trained on ImageNet).
* **Decoder:** U-Net (with skip connections for spatial accuracy).
* **Input Size:** 256x256 grayscale or RGB normalized tensors.
* **Loss Function:** Combination of BCE and Dice Loss for robust boundary detection.

---

## 🛠️ Tech Stack
* **Backend:** FastAPI (Asynchronous request handling).
* **Frontend:** Streamlit (Clinical dashboard).
* **Inference:** PyTorch (CPU-optimized for this version).
* **Image Processing:** OpenCV, Pillow, Matplotlib.
* **Data Handling:** NumPy 1.26.4 (Pinned for `.pkl` compatibility).

---

## ⚙️ Installation

### 1. System Requirements
* **Python 3.12.x** (Mandatory for dependency alignment).
* **Git** installed.

### 2. Environment Setup
Since we are using specific versions of Torch and NumPy to avoid "Header size" errors, run the following global install:

```powershell
pip install fastapi==0.111.0 uvicorn==0.30.0 python-multipart==0.0.9 jinja2==3.1.5 torch==2.1.0 segmentation-models-pytorch==0.3.3 Pillow==11.1.0 numpy==1.26.4 requests matplotlib streamlit
```

---

## 🚀 Usage

### 1. Run the FastAPI Backend
```bash
python -m uvicorn main:app --reload
```
Access Swagger UI at: `http://127.0.0.1:8000/docs`

### 2. Run the Streamlit UI
```bash
streamlit run app.py
```

---

## ⚖️ Threshold Configuration
The sensitivity of the model is controlled by the `best_threshold` variable in `main.py`. 

* **Default:** `0.86` (High Precision, fewer false alarms).
* **Adjustment:** Lowering this value (e.g., to `0.50`) increases **Recall**, making the model more likely to catch subtle cases at the risk of more false positives.

---

## 📂 Repository Structure
```text
.
├── main.py                # API Entry point & Inference logic
├── app.py                 # Streamlit UI Dashboard
├── pneumothorax_v1.pkl    # Model weights (Serialized)
├── requirements.txt       # Dependency manifest
└── README.md              # Project documentation
```

---

## 👨‍💻 Author
**Syed Mohammed Arsalan**
* GitHub: [@SyedmohammedArsalan](https://github.com/SyedmohammedArsalan)

---
*Disclaimer: This tool is for educational/research purposes only. Always consult a certified radiologist for medical diagnosis.*
```