# 🫁 PneumoAI: Full-Stack Pneumothorax Detection & Management System

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-05998B?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)

An advanced medical imaging platform that combines **Deep Learning** (U-Net + EfficientNet-B0) with a **Full-Stack Web Architecture** to detect, segment, and log Pneumothorax cases.

---

## 📖 Table of Contents
- [Project Overview](#project-overview)
- [System Architecture](#system-architecture)
- [Technical Stack](#technical-stack)
- [Installation](#installation)
- [Database Schema](#database-schema)
- [Usage](#usage)

---

## 🧐 Project Overview
Unlike standard AI scripts, PneumoAI is a persistent system. It not only detects lung collapse in real-time but also:
* **Stores History:** Logs every prediction in an integrated SQLite database.
* **Web UI:** Serves a dynamic frontend using Jinja2 templates and static assets.
* **Segmentation:** Provides pixel-level localization of pleural air leaks.

---

## 🏗️ System Architecture
The project follows a modular "Model-View-Controller" style pattern:
* **`main.py`**: The application kernel; handles routing and integration.
* **`model.py`**: Defines the Deep Learning architecture (SMP U-Net).
* **`database.py` & `schemas.py`**: Manages SQLAlchemy ORM and Pydantic data validation.
* **`utils.py`**: Helper functions for image processing and normalization.
* **`static/` & `templates/`**: Contains CSS/JS assets and HTML layouts.

---

## 🛠️ Technical Stack
* **Deep Learning:** PyTorch, Segmentation Models PyTorch (SMP).
* **Backend:** FastAPI, SQLAlchemy (ORM).
* **Database:** SQLite (`pneumoai.db`).
* **Frontend:** HTML5, CSS3, Jinja2 Templates.
* **Pinned Dependency:** NumPy 1.26.4 (Critical for model weight compatibility).

---

## ⚙️ Installation

### 1. Requirements
* **Python 3.12.x** * **OS:** Windows/Linux/MacOS

### 2. Setup
Clone the repo and install the optimized medical AI stack:
```powershell
pip install fastapi==0.111.0 uvicorn==0.30.0 sqlalchemy pydantic python-multipart jinja2 torch==2.1.0 segmentation-models-pytorch==0.3.3 Pillow==11.1.0 numpy==1.26.4 requests matplotlib
```

---

## 🗄️ Database Schema
The system uses a relational structure to track clinical findings:
* **Records Table:** Stores image IDs, timestamps, classification verdicts, and confidence scores.
* **Persistence:** All data is saved locally in `pneumoai.db` for later review or audit.

---

## 🚀 Usage

### Run the Web Server
Launch the full-stack application using Uvicorn:
```bash
python -m uvicorn main:app --reload
```

### Accessing the System
* **User Interface:** `http://127.0.0.1:8000/`
* **Interactive API Docs:** `http://127.0.0.1:8000/docs`

---

## 👨‍💻 Author
**Syed Mohammed Arsalan** *GitHub: [@SyedmohammedArsalan](https://github.com/SyedmohammedArsalan)*

---
*Disclaimer: This tool is for educational/research purposes. Always consult a certified radiologist for medical diagnosis.*
```

