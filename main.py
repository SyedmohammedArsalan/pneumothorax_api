import contextlib, io, os, shutil, uuid
import numpy as np   # <-- important fix
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from PIL import Image

from model    import ModelService
from database import init_db, save_scan, get_history, get_stats
from schemas  import PredictionResponse, StatsResponse
from utils    import make_overlay, make_heatmap, calculate_severity, _pil_to_b64
from auth import (
    UserRegister, UserLogin, Token,
    get_password_hash, verify_password,
    create_access_token, get_current_user, UserInDB,
    get_user_by_username, get_user_by_email, create_user
)
from llm_chatbot import get_llm_response
from pydantic import BaseModel
from interpretability import GradCAM, overlay_gradcam, reliability_badge

PKL_PATH = "pneumothorax_deployment_v1.pkl"
service  = ModelService()

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    service.load(PKL_PATH)
    yield

app = FastAPI(title="PneumoAI", version="2.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

os.makedirs("uploads", exist_ok=True)
app.mount("/static",  StaticFiles(directory="static"),  name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")


def get_service():
    if service.model is None:
        raise HTTPException(503, "Model not loaded.")
    return service


# =====================================================
# PUBLIC PAGES
# =====================================================
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# =====================================================
# AUTHENTICATION ENDPOINTS
# =====================================================
@app.post("/auth/register", response_model=Token)
async def register(user: UserRegister):
    if get_user_by_username(user.username):
        raise HTTPException(400, "Username already taken")
    if get_user_by_email(user.email):
        raise HTTPException(400, "Email already registered")
    hashed_pw = get_password_hash(user.password)
    user_id = create_user(user.username, user.email, hashed_pw)
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    db_user = get_user_by_username(user.username)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# =====================================================
# PROTECTED API ENDPOINTS
# =====================================================
@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": service.model is not None}

@app.get("/api/stats", response_model=StatsResponse)
async def stats(current_user: UserInDB = Depends(get_current_user)):
    return StatsResponse(**get_stats(user_id=current_user.id))

@app.get("/api/history")
async def history(current_user: UserInDB = Depends(get_current_user)):
    return get_history(20, user_id=current_user.id)

@app.get("/api/model_performance")
async def model_performance(current_user: UserInDB = Depends(get_current_user)):
    metrics = service.get_metrics()
    return {
        "dice": metrics.get("best_val_dice", 0.7921),
        "threshold": 0.86,
        "description": "Dice coefficient measures overlap between predicted and ground‑truth masks."
    }

@app.post("/api/predict", response_model=PredictionResponse)
async def predict(
    file: UploadFile = File(...),
    svc: ModelService = Depends(get_service),
    current_user: UserInDB = Depends(get_current_user),
):
    if file.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(422, "JPEG or PNG only.")

    raw = await file.read()
    try:
        pil_img = Image.open(io.BytesIO(raw))
    except Exception:
        raise HTTPException(400, "Cannot read image.")

    ext      = os.path.splitext(file.filename)[1] or ".png"
    fname    = f"{uuid.uuid4().hex}{ext}"
    fpath    = os.path.join("uploads", fname)
    with open(fpath, "wb") as f:
        f.write(raw)

    result  = svc.predict(pil_img)
    overlay = heatmap = None
    severity_info = None
    reliability = None
    gradcam_b64 = None

    if result["has_pneumothorax"]:
        overlay = make_overlay(pil_img, result["binary_mask"])
        heatmap = make_heatmap(result["prob_map"])
        severity_info = calculate_severity(result["binary_mask"])
        mask_area = int(np.sum(result["binary_mask"]))
        reliability = reliability_badge(result["confidence"], mask_area)

        # Grad‑CAM (classification explainability)
        try:
            print("--- Grad-CAM generation started ---")
            grad_layer = svc.get_gradcam_layer()
            print(f"Target layer: {grad_layer}")
            grad_cam = GradCAM(svc.model, grad_layer)
            tensor = svc.transform(pil_img.convert("RGB")).unsqueeze(0)
            cam = grad_cam.generate(tensor)
            print(f"CAM shape: {cam.shape}, min={cam.min():.3f}, max={cam.max():.3f}")
            gradcam_overlay = overlay_gradcam(pil_img, cam)
            gradcam_b64 = _pil_to_b64(gradcam_overlay)
            print(f"Grad-CAM base64 length: {len(gradcam_b64)}")
        except Exception as e:
            print(f"Grad-CAM failed: {e}")
            import traceback
            traceback.print_exc()
            gradcam_b64 = None

    verdict = (
        f"⚠️ Pneumothorax Detected — {result['confidence']*100:.1f}% confidence"
        if result["has_pneumothorax"]
        else f"✅ No Pneumothorax — {result['confidence']*100:.1f}% probability"
    )

    save_scan(file.filename, fpath, verdict,
              result["confidence"], result["has_pneumothorax"],
              user_id=current_user.id)

    scan_id = get_history(1, user_id=current_user.id)[0]["id"]

    return PredictionResponse(
        has_pneumothorax = result["has_pneumothorax"],
        confidence       = result["confidence"],
        verdict          = verdict,
        overlay_b64      = overlay,
        heatmap_b64      = heatmap,
        scan_id          = scan_id,
        severity         = severity_info,
        reliability      = reliability,
        gradcam_b64      = gradcam_b64,
    )

@app.get("/api/scan/{scan_id}/image")
def get_scan_image(scan_id: int, current_user: UserInDB = Depends(get_current_user)):
    import sqlite3
    con = sqlite3.connect("pneumoai.db")
    row = con.execute("SELECT filepath, user_id FROM scans WHERE id=?", (scan_id,)).fetchone()
    con.close()
    if not row or not os.path.exists(row[0]):
        raise HTTPException(404, "Not found.")
    if row[1] != current_user.id:
        raise HTTPException(403, "Access denied")
    return FileResponse(row[0])


# =====================================================
# CHATBOT ENDPOINT
# =====================================================
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    found_match: bool

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: UserInDB = Depends(get_current_user)):
    reply, found = get_llm_response(request.message)
    return ChatResponse(reply=reply, found_match=found)